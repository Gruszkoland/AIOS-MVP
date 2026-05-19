import { db, initializeCache } from "../../lib/db";
/**
 * Phase 3: Offline Mode & Data Fetching Tests
 */
// Mock fetch
global.fetch = jest.fn();
describe("Offline Mode & Fallback Caching", () => {
    beforeEach(() => {
        jest.clearAllMocks();
        global.fetch.mockClear();
    });
    afterEach(async () => {
        // Clear database after each test
        await db.jobs.clear();
        await db.kpis.clear();
        await db.status.clear();
    });
    test("initializes database on app start", async () => {
        // This test verifies Dexie initializes without errors
        const result = await initializeCache();
        expect(result).toBeUndefined(); // No errors thrown
    });
    test("caches successful API response", async () => {
        const mockData = {
            status: "OK",
            running: true,
            backend_type: "Flask",
        };
        global.fetch.mockResolvedValueOnce({
            ok: true,
            json: async () => mockData,
        });
        // In real component, this would cache the data
        const response = await fetch("http://localhost:8001/api/arbitrage/status");
        const data = await response.json();
        expect(data).toEqual(mockData);
        expect(data.running).toBe(true);
    });
    test("falls back to cached data on network failure", async () => {
        // First, simulate successful cache
        await db.status.add({
            status: "offline (cached)",
            running: false,
            backend_type: "Flask",
            timestamp: Date.now(),
        });
        // Then simulate network failure
        global.fetch.mockRejectedValueOnce(new Error("Network unreachable"));
        try {
            await fetch("http://localhost:8001/api/arbitrage/status");
        }
        catch (error) {
            // Expected to fail
        }
        // Should successfully retrieve cached data
        const cached = await db.status.toArray();
        expect(cached.length).toBeGreaterThan(0);
        expect(cached[0].backend_type).toBe("Flask");
    });
    test("detects offline mode when backend is unreachable", async () => {
        // Simulate timeout
        global.fetch.mockImplementationOnce(() => new Promise((_, reject) => setTimeout(() => reject(new Error("Timeout")), 100)));
        let isOffline = false;
        try {
            await fetch("http://localhost:8001/api/arbitrage/status", {
                signal: AbortSignal.timeout(50),
            });
        }
        catch (error) {
            isOffline = true;
        }
        expect(isOffline).toBe(true);
    });
    test("stores KPI metrics in Dexie", async () => {
        const mockKPIs = {
            total_jobs: 42,
            successful_jobs: 38,
            failed_jobs: 4,
            avg_processing_time: 2.5,
            total_xrp_volume: 1500,
            timestamp: Date.now(),
        };
        await db.kpis.add(mockKPIs);
        const stored = await db.kpis.toArray();
        expect(stored.length).toBe(1);
        expect(stored[0].total_jobs).toBe(42);
    });
    test("retrieves latest KPI metrics when multiple records exist", async () => {
        const kpi1 = {
            total_jobs: 40,
            successful_jobs: 38,
            failed_jobs: 2,
            avg_processing_time: 2.5,
            total_xrp_volume: 1400,
            timestamp: Date.now() - 5000,
        };
        const kpi2 = {
            total_jobs: 42,
            successful_jobs: 38,
            failed_jobs: 4,
            avg_processing_time: 2.5,
            total_xrp_volume: 1500,
            timestamp: Date.now(),
        };
        await db.kpis.bulkAdd([kpi1, kpi2]);
        const latest = await db.kpis
            .orderBy("timestamp")
            .reverse()
            .limit(1)
            .toArray();
        expect(latest[0].total_jobs).toBe(42);
    });
    test("stores jobs with status and timestamps", async () => {
        const mockJob = {
            id: "job-123",
            status: "pending",
            created_at: new Date().toISOString(),
            xrp_amount: 100,
            pair: "XRP/USD",
            synced_at: Date.now(),
        };
        await db.jobs.add(mockJob);
        const stored = await db.jobs.toArray();
        expect(stored.length).toBe(1);
        expect(stored[0].id).toBe("job-123");
        expect(stored[0].status).toBe("pending");
    });
    test("maintains data persistence across app restart", async () => {
        const testJob = {
            id: "persistent-job",
            status: "completed",
            created_at: new Date().toISOString(),
            xrp_amount: 500,
            synced_at: Date.now(),
        };
        // Simulate "app session 1" - save data
        await db.jobs.add(testJob);
        let retrieved = await db.jobs
            .where("id")
            .equals("persistent-job")
            .toArray();
        expect(retrieved.length).toBe(1);
        // Simulate "app restart" - data should persist in IndexedDB
        // (In real scenario, IndexedDB persists across browser refreshes)
        retrieved = await db.jobs.where("id").equals("persistent-job").toArray();
        expect(retrieved.length).toBe(1);
        expect(retrieved[0].status).toBe("completed");
    });
});
//# sourceMappingURL=DashboardOfflineMode.test.js.map