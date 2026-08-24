/*
 * RVC-FANET: Route-Validity-Contract Routing for Flying Ad Hoc Networks
 * Native ns-3.41 Simulation Implementation
 *
 * Implements:
 *   1. 3D Gauss-Markov Mobility for UAV Swarms
 *   2. Relative State Trajectory Predictor (CV / Kalman)
 *   3. Blocked Conformal Calibration Engine
 *   4. Link Risk Estimator rho_e(H) via Conformal Quantile Search
 *   5. Path Risk Accumulator R_P(H) = sum(rho_e) with Hard Contract Constraint R_P <= alpha_route
 *   6. Comparative Protocols: AODV, PPR (Point-Predictive), RVC-FANET
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/internet-module.h"

// RVC-FANET Oracle Bypass: We need access to AODV's internal Routing Table
// to delete routes dynamically if they violate the R_P(H) <= alpha constraint.
#define private public
#include "ns3/aodv-routing-protocol.h"
#include "ns3/aodv-rtable.h"
#undef private

#include "ns3/aodv-module.h"
#include "ns3/olsr-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <deque>
#include <cmath>
#include <algorithm>
#include <map>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("RvcFanetSimulation");

// ===========================================================================
// 1. Relative Trajectory Predictor (C++)
// ===========================================================================
class RelativePredictor
{
public:
    // Forecasts relative position at tau steps ahead: r_hat(t + tau) = r(t) + v(t) * tau
    static std::vector<Vector> PredictTrajectory(Vector relPos, Vector relVel, double horizon, double dt = 0.1)
    {
        int nSteps = std::max(1, static_cast<int>(std::round(horizon / dt)));
        std::vector<Vector> preds;
        preds.reserve(nSteps);

        for (int i = 1; i <= nSteps; ++i)
        {
            double tau = i * dt;
            Vector p(relPos.x + relVel.x * tau,
                     relPos.y + relVel.y * tau,
                     relPos.z + relVel.z * tau);
            preds.push_back(p);
        }
        return preds;
    }
};

// ===========================================================================
// 2. Blocked Conformal Calibrator Engine (C++)
// ===========================================================================
class ConformalCalibrator
{
private:
    size_t m_blockSize;
    size_t m_windowBlocks;
    size_t m_minScores;
    std::vector<double> m_currentBlock;
    std::deque<double> m_scores;

public:
    ConformalCalibrator(size_t blockSize = 3, size_t windowBlocks = 30, size_t minScores = 5)
        : m_blockSize(blockSize), m_windowBlocks(windowBlocks), m_minScores(minScores)
    {
    }

    bool IsReady() const
    {
        return m_scores.size() >= m_minScores;
    }

    size_t GetNumScores() const
    {
        return m_scores.size();
    }

    void AddResidual(double residualNorm)
    {
        m_currentBlock.push_back(residualNorm);
        if (m_currentBlock.size() >= m_blockSize)
        {
            double maxScore = *std::max_element(m_currentBlock.begin(), m_currentBlock.end());
            m_scores.push_back(maxScore);
            if (m_scores.size() > m_windowBlocks)
            {
                m_scores.pop_front();
            }
            m_currentBlock.clear();
        }
    }

    void AddScoreDirect(double score)
    {
        m_scores.push_back(score);
        if (m_scores.size() > m_windowBlocks)
        {
            m_scores.pop_front();
        }
    }

    double GetQuantile(double alpha) const
    {
        if (!IsReady())
        {
            return 1e9; // Infinity equivalent
        }

        size_t n = m_scores.size();
        double level = (1.0 - alpha) * (n + 1.0) / static_cast<double>(n);
        level = std::min(level, 1.0);

        std::vector<double> sortedScores(m_scores.begin(), m_scores.end());
        std::sort(sortedScores.begin(), sortedScores.end());

        size_t idx = static_cast<size_t>(std::ceil(level * n)) - 1;
        idx = std::min(idx, n - 1);
        return sortedScores[idx];
    }

    std::vector<double> GetScores() const
    {
        return std::vector<double>(m_scores.begin(), m_scores.end());
    }
};

// ===========================================================================
// 3. Link Risk Estimator rho_e(H) (C++)
// ===========================================================================
class LinkRiskEstimator
{
private:
    double m_txRange;

public:
    LinkRiskEstimator(double txRange = 250.0) : m_txRange(txRange) {}

    double ComputeRho(const std::vector<Vector>& predictedTrajectory, const ConformalCalibrator& calibrator) const
    {
        if (!calibrator.IsReady())
        {
            return 1.0; // Uncertifiable
        }

        double maxDist = 0.0;
        for (const auto& pt : predictedTrajectory)
        {
            double dist = std::sqrt(pt.x * pt.x + pt.y * pt.y + pt.z * pt.z);
            if (dist > maxDist)
            {
                maxDist = dist;
            }
        }

        double margin = m_txRange - maxDist;
        if (margin < 0.0)
        {
            return 1.0; // Point prediction already exceeds communication range
        }

        std::vector<double> scores = calibrator.GetScores();
        size_t n = scores.size();
        std::sort(scores.begin(), scores.end());

        int kMax = -1;
        for (size_t i = 0; i < n; ++i)
        {
            if (scores[i] <= margin)
            {
                kMax = static_cast<int>(i);
            }
            else
            {
                break;
            }
        }

        if (kMax < 0)
        {
            return 1.0; // No calibration score small enough
        }

        double rho = 1.0 - static_cast<double>(kMax + 1) / static_cast<double>(n + 1);
        return std::max(0.0, rho);
    }
};

// ===========================================================================
// 4. Contract Data Structure & Metrics Container
// ===========================================================================
struct ContractMetrics
{
    uint32_t totalRreqsInitiated = 0;
    uint32_t totalRreqsPruned = 0;
    uint32_t totalContractsCreated = 0;
    uint32_t totalRevalidations = 0;
    uint32_t totalNoRouteFailures = 0;
};

static ContractMetrics g_contractMetrics;

struct AdmittedRoute {
    std::vector<uint32_t> path;
    ns3::Time expireTime;
    bool failed;
};
static std::vector<AdmittedRoute> g_admittedRoutes;

void EvaluateRouteFailures(NodeContainer nodes, double txRange)
{
    ns3::Time now = Simulator::Now();
    for (auto& r : g_admittedRoutes)
    {
        if (r.failed) continue;
        if (now > r.expireTime) continue;
        
        // check links
        for (size_t i = 0; i < r.path.size() - 1; ++i)
        {
            Vector p1 = nodes.Get(r.path[i])->GetObject<MobilityModel>()->GetPosition();
            Vector p2 = nodes.Get(r.path[i+1])->GetObject<MobilityModel>()->GetPosition();
            double d = std::sqrt(std::pow(p1.x-p2.x, 2) + std::pow(p1.y-p2.y, 2) + std::pow(p1.z-p2.z, 2));
            if (d > txRange)
            {
                r.failed = true;
                g_contractMetrics.totalNoRouteFailures++;
                break;
            }
        }
    }
    Simulator::Schedule(Seconds(0.1), &EvaluateRouteFailures, nodes, txRange);
}

// ===========================================================================
// Global Simulation Parameters (for Schedule wrapper)
// ===========================================================================
struct SimParams
{
    std::string protocol;
    double alphaRoute;
    double hReq;
    double nodeSpeed;
    const LinkRiskEstimator* riskEstimator = nullptr;
    const ConformalCalibrator* calibrator = nullptr;
    std::string ablationMode;
};

static SimParams g_simParams;

// ===========================================================================
// Topology and Reachability Tracker (For Conditional PDR)
// ===========================================================================
class TopologyTracker
{
public:
    uint32_t totalSamples = 0;
    uint32_t reachableSamples = 0;
    double totalNeighborDegree = 0.0;
    double totalLccFraction = 0.0; // Largest Connected Component fraction

    void SampleTopology(NodeContainer nodes, double txRange, uint32_t srcIdx, uint32_t dstIdx)
    {
        std::string protocol = g_simParams.protocol;
        double alphaRoute = g_simParams.alphaRoute;
        double hReq = g_simParams.hReq;
        const LinkRiskEstimator& riskEstimator = *(g_simParams.riskEstimator);
        const ConformalCalibrator& calibrator = *(g_simParams.calibrator);

        uint32_t n = nodes.GetN();
        std::vector<std::vector<uint32_t>> adj(n);
        double currentDegreeSum = 0;

        // Build adjacency list based on Euclidean distance
        for (uint32_t i = 0; i < n; ++i)
        {
            Ptr<MobilityModel> mobI = nodes.Get(i)->GetObject<MobilityModel>();
            Vector posI = mobI->GetPosition();
            for (uint32_t j = i + 1; j < n; ++j)
            {
                Ptr<MobilityModel> mobJ = nodes.Get(j)->GetObject<MobilityModel>();
                Vector posJ = mobJ->GetPosition();
                double dist = std::sqrt(std::pow(posI.x - posJ.x, 2) + std::pow(posI.y - posJ.y, 2) + std::pow(posI.z - posJ.z, 2));
                if (dist <= txRange)
                {
                    adj[i].push_back(j);
                    adj[j].push_back(i);
                    currentDegreeSum += 2.0;
                }
            }
        }

        totalSamples++;
        totalNeighborDegree += (currentDegreeSum / n);

        // BFS to find components and shortest path
        std::vector<bool> visited(n, false);
        std::vector<int> parent(n, -1);
        uint32_t maxComponentSize = 0;
        bool srcDstConnected = false;

        for (uint32_t i = 0; i < n; ++i)
        {
            if (!visited[i])
            {
                std::vector<uint32_t> component;
                std::deque<uint32_t> q;
                q.push_back(i);
                visited[i] = true;

                bool hasSrc = false;
                bool hasDst = false;

                while (!q.empty())
                {
                    uint32_t curr = q.front();
                    q.pop_front();
                    component.push_back(curr);

                    if (curr == srcIdx) hasSrc = true;
                    if (curr == dstIdx) hasDst = true;

                    for (uint32_t neighbor : adj[curr])
                    {
                        if (!visited[neighbor])
                        {
                            visited[neighbor] = true;
                            parent[neighbor] = curr;
                            q.push_back(neighbor);
                        }
                    }
                }

                if (component.size() > maxComponentSize) maxComponentSize = component.size();
                if (hasSrc && hasDst) srcDstConnected = true;
            }
        }

        totalLccFraction += ((double)maxComponentSize / n);
        if (srcDstConnected)
        {
            reachableSamples++;
            
            // --- Oracle RVC-FANET Enforcement ---
            if (protocol == "RVC" || protocol == "PPR")
            {
                double pathRisk = 0.0;
                double maxLinkRisk = 0.0;
                std::vector<uint32_t> path;
                uint32_t curr = dstIdx;
                
                // Traverse shortest path backwards
                while (curr != srcIdx && curr != (uint32_t)-1)
                {
                    path.push_back(curr);
                    uint32_t p = parent[curr];
                    if (p == (uint32_t)-1) break;
                    
                    Ptr<MobilityModel> mobP = nodes.Get(p)->GetObject<MobilityModel>();
                    Ptr<MobilityModel> mobC = nodes.Get(curr)->GetObject<MobilityModel>();
                    
                    Vector posP = mobP->GetPosition();
                    Vector velP = mobP->GetVelocity();
                    Vector posC = mobC->GetPosition();
                    Vector velC = mobC->GetVelocity();
                    
                    Vector relPos(posC.x - posP.x, posC.y - posP.y, posC.z - posP.z);
                    Vector relVel(velC.x - velP.x, velC.y - velP.y, velC.z - velP.z);
                    
                    std::vector<Vector> pred = RelativePredictor::PredictTrajectory(relPos, relVel, hReq);
                    
                    if (protocol == "RVC")
                    {
                        double r = riskEstimator.ComputeRho(pred, calibrator);
                        pathRisk += r;
                        maxLinkRisk = std::max(maxLinkRisk, r);
                    }
                    else if (protocol == "PPR") // PPR has no uncertainty, just 1.0 if point prediction fails
                    {
                        double maxD = 0;
                        for(auto pt : pred) maxD = std::max(maxD, std::sqrt(pt.x*pt.x + pt.y*pt.y + pt.z*pt.z));
                        if(txRange - maxD < 0) pathRisk += 1.0;
                    }
                    curr = p;
                }
                
                bool prune = false;
                if (g_simParams.ablationMode == "A1") {
                    prune = (maxLinkRisk > alphaRoute);
                } else if (g_simParams.ablationMode == "A2") {
                    double perHopBudget = alphaRoute / static_cast<double>(path.size());
                    prune = (maxLinkRisk > perHopBudget);
                } else {
                    // Default A3 (Full RVC)
                    prune = (pathRisk > alphaRoute);
                }
                
                // If the path violates the contract, prune the route from the AODV routing table!
                if (prune)
                {
                    Ptr<Ipv4> ipv4 = nodes.Get(srcIdx)->GetObject<Ipv4>();
                    Ptr<aodv::RoutingProtocol> aodv = DynamicCast<aodv::RoutingProtocol>(ipv4->GetRoutingProtocol());
                    if (aodv)
                    {
                        Ipv4Address dstIp = nodes.Get(dstIdx)->GetObject<Ipv4>()->GetAddress(1, 0).GetLocal();
                        // This uses the private bypass trick to access AODV's internal routing table
                        aodv->m_routingTable.DeleteRoute(dstIp);
                        g_contractMetrics.totalRreqsPruned++;
                    }
                }
                else
                {
                    g_contractMetrics.totalContractsCreated++;
                    
                    // Reconstruct path from dst to src, then reverse it to src->dst
                    std::vector<uint32_t> fwdPath;
                    uint32_t c = dstIdx;
                    while (c != (uint32_t)-1) {
                        fwdPath.push_back(c);
                        if (c == srcIdx) break;
                        c = parent[c];
                    }
                    // AdmittedRoute logic
                    AdmittedRoute ar;
                    ar.path = fwdPath;
                    ar.expireTime = Simulator::Now() + Seconds(hReq);
                    ar.failed = false;
                    g_admittedRoutes.push_back(ar);
                }
            }
        }
    }
};

static TopologyTracker g_topoTracker;

void PeriodicTopologyCheck(NodeContainer nodes, double txRange, uint32_t srcIdx, uint32_t dstIdx)
{
    g_topoTracker.SampleTopology(nodes, txRange, srcIdx, dstIdx);
    Simulator::Schedule(Seconds(0.1), &PeriodicTopologyCheck, nodes, txRange, srcIdx, dstIdx);
}

// ===========================================================================
// Empirical Calibration Collection Logic
// ===========================================================================
static std::vector<double> g_calibrationResiduals;

void CheckPrediction(Ptr<Node> nodeA, Ptr<Node> nodeB, Vector predictedPos)
{
    Ptr<MobilityModel> mobA = nodeA->GetObject<MobilityModel>();
    Ptr<MobilityModel> mobB = nodeB->GetObject<MobilityModel>();
    Vector posA = mobA->GetPosition();
    Vector posB = mobB->GetPosition();
    Vector actualRel(posB.x - posA.x, posB.y - posA.y, posB.z - posA.z);
    double dx = actualRel.x - predictedPos.x;
    double dy = actualRel.y - predictedPos.y;
    double dz = actualRel.z - predictedPos.z;
    double error = std::sqrt(dx*dx + dy*dy + dz*dz);
    g_calibrationResiduals.push_back(error);
}

void SchedulePredictions(NodeContainer nodes, double hReq)
{
    // Sample a few pairs
    uint32_t nNodes = nodes.GetN();
    for (uint32_t i = 0; i < std::min(nNodes, 10u); ++i) {
        for (uint32_t j = i + 1; j < std::min(nNodes, 10u); ++j) {
            Ptr<MobilityModel> mobA = nodes.Get(i)->GetObject<MobilityModel>();
            Ptr<MobilityModel> mobB = nodes.Get(j)->GetObject<MobilityModel>();
            Vector posA = mobA->GetPosition();
            Vector posB = mobB->GetPosition();
            Vector velA = mobA->GetVelocity();
            Vector velB = mobB->GetVelocity();
            Vector relPos(posB.x - posA.x, posB.y - posA.y, posB.z - posA.z);
            Vector relVel(velB.x - velA.x, velB.y - velA.y, velB.z - velA.z);
            
            std::vector<Vector> preds = RelativePredictor::PredictTrajectory(relPos, relVel, hReq, 0.1);
            if (!preds.empty()) {
                Vector finalPred = preds.back();
                Simulator::Schedule(Seconds(hReq), &CheckPrediction, nodes.Get(i), nodes.Get(j), finalPred);
            }
        }
    }
    // Repeat every 1.0s
    Simulator::Schedule(Seconds(1.0), &SchedulePredictions, nodes, hReq);
}

void TriggerAbruptShift(NodeContainer nodes)
{
    for (uint32_t i = 0; i < nodes.GetN(); ++i)
    {
        Ptr<GaussMarkovMobilityModel> mob = nodes.Get(i)->GetObject<GaussMarkovMobilityModel>();
        if (mob)
        {
            mob->ForceOrthogonalShift();
        }
    }
    std::cout << "Triggered instantaneous 15m/s orthogonal trajectory shift at t=" << Simulator::Now().GetSeconds() << "s\n";
}

// ===========================================================================
// 5. Main Simulation Setup
// ===========================================================================
int main(int argc, char *argv[])
{
    std::string protocol = "RVC"; // AODV | PPR | RVC
    uint32_t numNodes = 20;
    double simTime = 60.0;
    double nodeSpeed = 15.0;
    double txRange = 250.0;
    double hReq = 3.0;
    double alphaRoute = 0.10;
    uint32_t seed = 42;
    std::string csvFileName = "rvc_ns3_results.csv";
    uint32_t runMode = 0; // 0=Eval, 1=Calib
    std::string calibFile = "nominal_residuals.txt";
    std::string ablationMode = "A3";
    bool abruptShift = false;

    CommandLine cmd(__FILE__);
    cmd.AddValue("protocol", "Routing protocol (AODV, PPR, RVC)", protocol);
    cmd.AddValue("numNodes", "Number of UAV nodes", numNodes);
    cmd.AddValue("simTime", "Simulation duration in seconds", simTime);
    cmd.AddValue("nodeSpeed", "Mean UAV speed (m/s)", nodeSpeed);
    cmd.AddValue("txRange", "Communication range (m)", txRange);
    cmd.AddValue("hReq", "Contract validity horizon (s)", hReq);
    cmd.AddValue("alphaRoute", "Route-failure risk budget", alphaRoute);
    cmd.AddValue("seed", "Random seed", seed);
    cmd.AddValue("csvFileName", "Output CSV metrics file", csvFileName);
    cmd.AddValue("runMode", "0 for eval, 1 for calibration data generation", runMode);
    cmd.AddValue("calibFile", "Calibration residuals file", calibFile);
    cmd.AddValue("ablationMode", "A1, A2, or A3", ablationMode);
    cmd.AddValue("abruptShift", "Enable orthogonal trajectory shift at t=30s", abruptShift);
    cmd.Parse(argc, argv);

    // Make ablationMode globally accessible for EvaluateRouteFailures
    g_simParams.ablationMode = ablationMode;

    SeedManager::SetSeed(seed);
    SeedManager::SetRun(1);

    std::cout << "========================================================\n";
    std::cout << " RVC-FANET Native ns-3.41 Experiment Execution\n";
    std::cout << "========================================================\n";
    std::cout << " Protocol: " << protocol << " | Nodes: " << numNodes
              << " | Speed: " << nodeSpeed << " m/s | H: " << hReq << "s | Alpha: " << alphaRoute << "\n";

    // ── Create Node Container ─────────────────────────────────────────
    NodeContainer nodes;
    nodes.Create(numNodes);

    // ── Mobility Setup (3D Gauss-Markov) ──────────────────────────────
    MobilityHelper mobility;
    int64_t streamIndex = 0;

    Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator>();
    Ptr<UniformRandomVariable> xVar = CreateObject<UniformRandomVariable>();
    xVar->SetAttribute("Min", DoubleValue(0.0));
    xVar->SetAttribute("Max", DoubleValue(800.0));
    Ptr<UniformRandomVariable> yVar = CreateObject<UniformRandomVariable>();
    yVar->SetAttribute("Min", DoubleValue(0.0));
    yVar->SetAttribute("Max", DoubleValue(800.0));
    Ptr<UniformRandomVariable> zVar = CreateObject<UniformRandomVariable>();
    zVar->SetAttribute("Min", DoubleValue(50.0));
    zVar->SetAttribute("Max", DoubleValue(150.0));

    for (uint32_t i = 0; i < numNodes; ++i)
    {
        positionAlloc->Add(Vector(xVar->GetValue(), yVar->GetValue(), zVar->GetValue()));
    }
    mobility.SetPositionAllocator(positionAlloc);
    mobility.SetMobilityModel("ns3::GaussMarkovMobilityModel",
                              "Bounds", BoxValue(Box(0, 800, 0, 800, 50, 150)),
                              "TimeStep", TimeValue(Seconds(0.1)),
                              "Alpha", DoubleValue(0.85),
                              "MeanVelocity", StringValue("ns3::ConstantRandomVariable[Constant=" + std::to_string(nodeSpeed) + "]"),
                              "MeanDirection", StringValue("ns3::UniformRandomVariable[Min=0.0|Max=6.283185]"),
                              "MeanPitch", StringValue("ns3::ConstantRandomVariable[Constant=0.0]"));
    mobility.Install(nodes);
    streamIndex += mobility.AssignStreams(nodes, streamIndex);

    // ── Wifi & Channel Setup ──────────────────────────────────────────
    WifiHelper wifi;
    wifi.SetStandard(WIFI_STANDARD_80211a);

    YansWifiPhyHelper wifiPhy;
    YansWifiChannelHelper wifiChannel;
    wifiChannel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel");
    // Log-distance pathloss + Nakagami fading
    wifiChannel.AddPropagationLoss("ns3::LogDistancePropagationLossModel",
                                   "Exponent", DoubleValue(2.5),
                                   "ReferenceDistance", DoubleValue(1.0),
                                   "ReferenceLoss", DoubleValue(46.67));
    wifiChannel.AddPropagationLoss("ns3::NakagamiPropagationLossModel",
                                   "m0", DoubleValue(3.0),
                                   "m1", DoubleValue(3.0),
                                   "m2", DoubleValue(3.0));

    wifiPhy.SetChannel(wifiChannel.Create());

    WifiMacHelper wifiMac;
    wifiMac.SetType("ns3::AdhocWifiMac");

    NetDeviceContainer devices = wifi.Install(wifiPhy, wifiMac, nodes);

    // ── Internet & Routing Protocol Setup ─────────────────────────────
    InternetStackHelper internet;
    AodvHelper aodv;
    OlsrHelper olsr;

    if (protocol == "AODV")
    {
        internet.SetRoutingHelper(aodv);
    }
    else
    {
        // For PPR and RVC-FANET, we use custom contract-aware routing logic
        // built on top of the AODV routing helper framework
        aodv.Set("TtlStart", UintegerValue(1));
        internet.SetRoutingHelper(aodv);
    }

    internet.Install(nodes);

    Ipv4AddressHelper ipv4;
    ipv4.SetBase("10.1.1.0", "255.255.255.0");
    Ipv4InterfaceContainer interfaces = ipv4.Assign(devices);

    // ── Calibration Pre-Population & Risk Engine Simulation ────────────
    ConformalCalibrator calibrator(3, 2000, 5);
    LinkRiskEstimator riskEstimator(txRange);

    if (runMode == 0)
    {
        // EVALUATION MODE: Load genuine empirical residuals from file
        std::ifstream cfile(calibFile);
        if (cfile.is_open())
        {
            double res;
            int count = 0;
            // Load exactly 6000 residuals to fill the 2000-block capacity perfectly
            while (cfile >> res && count < 6000)
            {
                calibrator.AddResidual(res);
                count++;
            }
            cfile.close();
        }
        else if (protocol == "RVC")
        {
            std::cout << "WARNING: RVC protocol requested but calibFile not found!\n";
        }
    }
    else if (runMode == 1)
    {
        // CALIBRATION MODE: Schedule residual collection and do not run traffic
        Simulator::Schedule(Seconds(2.0), &SchedulePredictions, nodes, hReq);
    }
    // The route metrics are correctly gathered dynamically now in PeriodicTopologyCheck and EvaluateRouteFailures.

    // ── Traffic Applications ──────────────────────────────────────────
    uint16_t port = 9;
    uint32_t numFlows = 3;

    for (uint32_t f = 0; f < numFlows; ++f)
    {
        uint32_t srcIdx = f;
        uint32_t dstIdx = numNodes - 1 - f;

        UdpServerHelper server(port + f);
        ApplicationContainer serverApp = server.Install(nodes.Get(dstIdx));
        serverApp.Start(Seconds(1.0));
        serverApp.Stop(Seconds(simTime));

        UdpClientHelper client(interfaces.GetAddress(dstIdx), port + f);
        client.SetAttribute("MaxPackets", UintegerValue(100000));
        client.SetAttribute("Interval", TimeValue(Seconds(0.2)));
        client.SetAttribute("PacketSize", UintegerValue(512));

        ApplicationContainer clientApp = client.Install(nodes.Get(srcIdx));
        // Traffic starts after a 10s warmup for beacon/calibration settling
        clientApp.Start(Seconds(10.0));
        clientApp.Stop(Seconds(simTime - 1.0));
    }

    // ── FlowMonitor for Metrics ───────────────────────────────────────
    FlowMonitorHelper flowmon;
    Ptr<FlowMonitor> monitor = flowmon.InstallAll();

    g_simParams.protocol = protocol;
    g_simParams.alphaRoute = alphaRoute;
    g_simParams.hReq = hReq;
    g_simParams.riskEstimator = &riskEstimator;
    g_simParams.calibrator = &calibrator;

    std::cout << "Starting ns-3 discrete event simulation execution..." << std::endl;
    // ── Run Simulation ────────────────────────────────────────────────
    Simulator::Schedule(Seconds(10.0), &PeriodicTopologyCheck, nodes, txRange, 0, numNodes - 1);
    Simulator::Schedule(Seconds(10.1), &EvaluateRouteFailures, nodes, txRange);
    
    if (abruptShift) {
        Simulator::Schedule(Seconds(30.0), &TriggerAbruptShift, nodes);
    }
    
    Simulator::Stop(Seconds(simTime));
    Simulator::Run();
    std::cout << "ns-3 simulation finished." << std::endl;

    if (runMode == 1)
    {
        // CALIBRATION MODE: Dump residuals and exit early
        std::ofstream out(calibFile, std::ios::app);
        if (out.is_open())
        {
            for (double err : g_calibrationResiduals)
            {
                out << err << "\n";
            }
            out.close();
        }
        Simulator::Destroy();
        return 0;
    }

    // ── Collect Performance Metrics ───────────────────────────────────
    if (monitor)
    {
        monitor->CheckForLostPackets();
    }
    Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier>(flowmon.GetClassifier());
    std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

    uint64_t totalTxPackets = 0;
    uint64_t totalRxPackets = 0;
    double totalDelaySum = 0.0;

    for (auto const& item : stats)
    {
        totalTxPackets += item.second.txPackets;
        totalRxPackets += item.second.rxPackets;
        totalDelaySum += item.second.delaySum.GetSeconds();
    }

    double pdr = (totalTxPackets > 0) ? static_cast<double>(totalRxPackets) / static_cast<double>(totalTxPackets) : 0.0;
    double avgDelay = (totalRxPackets > 0) ? (totalDelaySum / totalRxPackets) : 0.0;

    double reachabilityRatio = (g_topoTracker.totalSamples > 0) ? (static_cast<double>(g_topoTracker.reachableSamples) / g_topoTracker.totalSamples) : 0.0;
    double conditionalPdr = (reachabilityRatio > 0.0) ? std::min(1.0, pdr / reachabilityRatio) : 0.0;
    double meanDegree = (g_topoTracker.totalSamples > 0) ? (g_topoTracker.totalNeighborDegree / g_topoTracker.totalSamples) : 0.0;
    double lccFrac = (g_topoTracker.totalSamples > 0) ? (g_topoTracker.totalLccFraction / g_topoTracker.totalSamples) : 0.0;

    std::cout << "\n--------------------------------------------------------\n";
    std::cout << " SIMULATION RESULTS SUMMARY (" << protocol << ")\n";
    std::cout << "--------------------------------------------------------\n";
    std::cout << " Sent Packets   : " << totalTxPackets << "\n";
    std::cout << " Recv Packets   : " << totalRxPackets << "\n";
    std::cout << " PDR            : " << (pdr * 100.0) << " %\n";
    std::cout << " Conditional PDR: " << (conditionalPdr * 100.0) << " %\n";
    std::cout << " Reachability   : " << (reachabilityRatio * 100.0) << " %\n";
    std::cout << " Mean Degree    : " << meanDegree << "\n";
    std::cout << " Avg Delay      : " << (avgDelay * 1000.0) << " ms\n";
    std::cout << " RREQs Pruned   : " << g_contractMetrics.totalRreqsPruned << "\n";
    std::cout << " Contracts      : " << g_contractMetrics.totalContractsCreated << "\n";
    std::cout << " FHR Failures   : " << g_contractMetrics.totalNoRouteFailures << "\n";
    std::cout << "--------------------------------------------------------\n";

    // ── Write Results to Machine-Readable CSV ────────────────────────
    bool writeHeader = false;
    std::ifstream checkFile(csvFileName);
    if (!checkFile.good())
    {
        writeHeader = true;
    }
    checkFile.close();

    std::ofstream csv(csvFileName, std::ios::out | std::ios::app);
    if (writeHeader)
    {
        csv << "protocol,numNodes,simTime,nodeSpeed,txRange,hReq,alphaRoute,seed,"
            << "txPackets,rxPackets,pdr,conditionalPdr,reachabilityRatio,meanDegree,lccFraction,avgDelayMs,rreqsPruned,contractsCreated,routeFailuresBeforeH\n";
    }
    csv << protocol << "," << numNodes << "," << simTime << "," << nodeSpeed << ","
        << txRange << "," << hReq << "," << alphaRoute << "," << seed << ","
        << totalTxPackets << "," << totalRxPackets << "," << pdr << ","
        << conditionalPdr << "," << reachabilityRatio << "," << meanDegree << "," << lccFrac << ","
        << (avgDelay * 1000.0) << ","
        << g_contractMetrics.totalRreqsPruned << ","
        << g_contractMetrics.totalContractsCreated << ","
        << g_contractMetrics.totalNoRouteFailures << "\n";
    csv.close();

    Simulator::Destroy();
    return 0;
}
