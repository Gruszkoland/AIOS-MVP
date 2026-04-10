import { render, screen } from "@testing-library/react";
import type { Job } from "../../components/JobTable";
import { JobTable } from "../../components/JobTable";
import {
    HealthStatus,
    LiveMetricsGrid,
    MetricCard,
} from "../../components/LiveMetricsCard";

/**
 * Phase 3: Component UI Tests
 */

describe("LiveMetricsCard Component", () => {
  test("renders metric card with values and units", () => {
    render(
      <MetricCard
        title="Total Jobs"
        value={42}
        unit="jobs"
        color="blue"
        icon="📊"
      />,
    );

    expect(screen.getByText("Total Jobs")).toBeInTheDocument();
    expect(screen.getByText("42")).toBeInTheDocument();
    expect(screen.getByText("jobs")).toBeInTheDocument();
    expect(screen.getByText("📊")).toBeInTheDocument();
  });

  test("displays trend indicator", () => {
    render(
      <MetricCard
        title="Successful Jobs"
        value={38}
        trend="up"
        color="green"
        icon="✅"
      />,
    );

    expect(screen.getByText(/↑/)).toBeInTheDocument();
    expect(screen.getByText(/Increasing/i)).toBeInTheDocument();
  });

  test("applies correct color styling", () => {
    const { container } = render(
      <MetricCard title="Failed Jobs" value={4} color="red" icon="❌" />,
    );

    const card = container.querySelector(".border-red-500");
    expect(card).toBeInTheDocument();
  });
});

describe("LiveMetricsGrid Component", () => {
  test("renders loading skeleton when loading", () => {
    render(<LiveMetricsGrid metrics={[]} isLoading={true} />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });

  test("displays offline indicator when offline", () => {
    render(
      <LiveMetricsGrid
        metrics={[{ title: "Test", value: 100, color: "blue" }]}
        isOffline={true}
      />,
    );

    expect(screen.getByText(/Using cached data/i)).toBeInTheDocument();
    expect(screen.getByText("🟢")).toBeInTheDocument(); // offline icon
  });

  test("renders multiple metrics in responsive grid", () => {
    const metrics = [
      { title: "Metric 1", value: 10, color: "blue" as const },
      { title: "Metric 2", value: 20, color: "green" as const },
      { title: "Metric 3", value: 30, color: "red" as const },
    ];

    render(<LiveMetricsGrid metrics={metrics} />);

    expect(screen.getByText("Metric 1")).toBeInTheDocument();
    expect(screen.getByText("Metric 2")).toBeInTheDocument();
    expect(screen.getByText("Metric 3")).toBeInTheDocument();
  });
});

describe("HealthStatus Component", () => {
  test("displays healthy status", () => {
    render(<HealthStatus backendHealth="healthy" lastUpdate={new Date()} />);

    expect(screen.getByText("🟢")).toBeInTheDocument();
    expect(screen.getByText(/Healthy/)).toBeInTheDocument();
  });

  test("displays degraded status", () => {
    render(<HealthStatus backendHealth="degraded" lastUpdate={new Date()} />);

    expect(screen.getByText("🟡")).toBeInTheDocument();
    expect(screen.getByText(/Degraded/)).toBeInTheDocument();
  });

  test("displays offline status with error message", () => {
    render(
      <HealthStatus
        backendHealth="offline"
        lastUpdate={new Date()}
        errorMessage="Backend unreachable"
      />,
    );

    expect(screen.getByText("🔴")).toBeInTheDocument();
    expect(screen.getByText(/Offline/)).toBeInTheDocument();
    expect(screen.getByText("Backend unreachable")).toBeInTheDocument();
  });
});

describe("JobTable Component", () => {
  const mockJobs: Job[] = [
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
    render(<JobTable jobs={mockJobs} />);

    expect(screen.getByText("Job ID")).toBeInTheDocument();
    expect(screen.getByText("Name")).toBeInTheDocument();
    expect(screen.getByText("Status")).toBeInTheDocument();
  });

  test("displays job rows with data", () => {
    render(<JobTable jobs={mockJobs} />);

    expect(screen.getByText("Arbitrage Job 1")).toBeInTheDocument();
    expect(screen.getByText("Arbitrage Job 2")).toBeInTheDocument();
  });

  test("shows progress bar for running jobs", () => {
    render(<JobTable jobs={mockJobs} />);

    // Find progress bar container for running job
    const progressElements = document.querySelectorAll(".h-full.bg-blue-500");
    expect(progressElements.length).toBeGreaterThan(0);
  });

  test("displays correct status badges", () => {
    render(<JobTable jobs={mockJobs} />);

    expect(screen.getByText("🔄")).toBeInTheDocument(); // running icon
    expect(screen.getByText("✅")).toBeInTheDocument(); // completed icon
  });

  test("shows no jobs message when jobs array is empty", () => {
    render(<JobTable jobs={[]} />);

    expect(screen.getByText("No jobs found")).toBeInTheDocument();
    expect(screen.getByText(/Create a new job/i)).toBeInTheDocument();
  });

  test("displays loading skeleton when loading", () => {
    render(<JobTable jobs={[]} isLoading={true} />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });

  test("triggers callback on job click", () => {
    const mockCallback = jest.fn();
    render(<JobTable jobs={mockJobs} onJobClick={mockCallback} />);

    const viewButtons = screen.getAllByText("View");
    viewButtons[0].click();

    expect(mockCallback).toHaveBeenCalledWith(
      expect.objectContaining({
        id: "job-1",
        name: "Arbitrage Job 1",
      }),
    );
  });
});
