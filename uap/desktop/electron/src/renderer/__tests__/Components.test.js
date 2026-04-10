import { jsx as _jsx } from "react/jsx-runtime";
import { render, screen } from "@testing-library/react";
import { JobTable } from "../../components/JobTable";
import { HealthStatus, LiveMetricsGrid, MetricCard, } from "../../components/LiveMetricsCard";
/**
 * Phase 3: Component UI Tests
 */
describe("LiveMetricsCard Component", () => {
    test("renders metric card with values and units", () => {
        render(_jsx(MetricCard, { title: "Total Jobs", value: 42, unit: "jobs", color: "blue", icon: "\uD83D\uDCCA" }));
        expect(screen.getByText("Total Jobs")).toBeInTheDocument();
        expect(screen.getByText("42")).toBeInTheDocument();
        expect(screen.getByText("jobs")).toBeInTheDocument();
        expect(screen.getByText("📊")).toBeInTheDocument();
    });
    test("displays trend indicator", () => {
        render(_jsx(MetricCard, { title: "Successful Jobs", value: 38, trend: "up", color: "green", icon: "\u2705" }));
        expect(screen.getByText(/↑/)).toBeInTheDocument();
        expect(screen.getByText(/Increasing/i)).toBeInTheDocument();
    });
    test("applies correct color styling", () => {
        const { container } = render(_jsx(MetricCard, { title: "Failed Jobs", value: 4, color: "red", icon: "\u274C" }));
        const card = container.querySelector(".border-red-500");
        expect(card).toBeInTheDocument();
    });
});
describe("LiveMetricsGrid Component", () => {
    test("renders loading skeleton when loading", () => {
        render(_jsx(LiveMetricsGrid, { metrics: [], isLoading: true }));
        const skeleton = document.querySelector(".animate-pulse");
        expect(skeleton).toBeInTheDocument();
    });
    test("displays offline indicator when offline", () => {
        render(_jsx(LiveMetricsGrid, { metrics: [{ title: "Test", value: 100, color: "blue" }], isOffline: true }));
        expect(screen.getByText(/Using cached data/i)).toBeInTheDocument();
        expect(screen.getByText("🟢")).toBeInTheDocument(); // offline icon
    });
    test("renders multiple metrics in responsive grid", () => {
        const metrics = [
            { title: "Metric 1", value: 10, color: "blue" },
            { title: "Metric 2", value: 20, color: "green" },
            { title: "Metric 3", value: 30, color: "red" },
        ];
        render(_jsx(LiveMetricsGrid, { metrics: metrics }));
        expect(screen.getByText("Metric 1")).toBeInTheDocument();
        expect(screen.getByText("Metric 2")).toBeInTheDocument();
        expect(screen.getByText("Metric 3")).toBeInTheDocument();
    });
});
describe("HealthStatus Component", () => {
    test("displays healthy status", () => {
        render(_jsx(HealthStatus, { backendHealth: "healthy", lastUpdate: new Date() }));
        expect(screen.getByText("🟢")).toBeInTheDocument();
        expect(screen.getByText(/Healthy/)).toBeInTheDocument();
    });
    test("displays degraded status", () => {
        render(_jsx(HealthStatus, { backendHealth: "degraded", lastUpdate: new Date() }));
        expect(screen.getByText("🟡")).toBeInTheDocument();
        expect(screen.getByText(/Degraded/)).toBeInTheDocument();
    });
    test("displays offline status with error message", () => {
        render(_jsx(HealthStatus, { backendHealth: "offline", lastUpdate: new Date(), errorMessage: "Backend unreachable" }));
        expect(screen.getByText("🔴")).toBeInTheDocument();
        expect(screen.getByText(/Offline/)).toBeInTheDocument();
        expect(screen.getByText("Backend unreachable")).toBeInTheDocument();
    });
});
describe("JobTable Component", () => {
    const mockJobs = [
        {
            id: "job-1",
            name: "Arbitrage Job 1",
            status: "running",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            progress: 50,
        },
        {
            id: "job-2",
            name: "Arbitrage Job 2",
            status: "completed",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        },
    ];
    test("renders job table with headers", () => {
        render(_jsx(JobTable, { jobs: mockJobs }));
        expect(screen.getByText("Job ID")).toBeInTheDocument();
        expect(screen.getByText("Name")).toBeInTheDocument();
        expect(screen.getByText("Status")).toBeInTheDocument();
    });
    test("displays job rows with data", () => {
        render(_jsx(JobTable, { jobs: mockJobs }));
        expect(screen.getByText("Arbitrage Job 1")).toBeInTheDocument();
        expect(screen.getByText("Arbitrage Job 2")).toBeInTheDocument();
    });
    test("shows progress bar for running jobs", () => {
        render(_jsx(JobTable, { jobs: mockJobs }));
        // Find progress bar container for running job
        const progressElements = document.querySelectorAll(".h-full.bg-blue-500");
        expect(progressElements.length).toBeGreaterThan(0);
    });
    test("displays correct status badges", () => {
        render(_jsx(JobTable, { jobs: mockJobs }));
        expect(screen.getByText("🔄")).toBeInTheDocument(); // running icon
        expect(screen.getByText("✅")).toBeInTheDocument(); // completed icon
    });
    test("shows no jobs message when jobs array is empty", () => {
        render(_jsx(JobTable, { jobs: [] }));
        expect(screen.getByText("No jobs found")).toBeInTheDocument();
        expect(screen.getByText(/Create a new job/i)).toBeInTheDocument();
    });
    test("displays loading skeleton when loading", () => {
        render(_jsx(JobTable, { jobs: [], isLoading: true }));
        const skeleton = document.querySelector(".animate-pulse");
        expect(skeleton).toBeInTheDocument();
    });
    test("triggers callback on job click", () => {
        const mockCallback = jest.fn();
        render(_jsx(JobTable, { jobs: mockJobs, onJobClick: mockCallback }));
        const viewButtons = screen.getAllByText("View");
        viewButtons[0].click();
        expect(mockCallback).toHaveBeenCalledWith(expect.objectContaining({
            id: "job-1",
            name: "Arbitrage Job 1",
        }));
    });
});
//# sourceMappingURL=Components.test.js.map