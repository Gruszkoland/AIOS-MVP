import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "../App";

/**
 * Phase 3: React Router Navigation Tests
 */

describe("App Navigation", () => {
  test("renders main navigation bar with all links", () => {
    render(<App />);

    expect(screen.getByText("ADRIAN 369")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Jobs/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Settings/i })).toBeInTheDocument();
  });

  test("navigates to dashboard when dashboard link is clicked", async () => {
    const user = userEvent.setup();
    render(<App />);

    const dashboardLink = screen.getByRole("link", { name: /Dashboard/i });
    await user.click(dashboardLink);

    // Dashboard should be visible - check for page-specific content
    expect(screen.getByText(/Real-time arbitrage monitoring/i)).toBeInTheDocument();
  });

  test("navigates to jobs page when jobs link is clicked", async () => {
    const user = userEvent.setup();
    render(<App />);

    const jobsLink = screen.getByRole("link", { name: /Jobs/i });
    await user.click(jobsLink);

    // JobsPage should be visible
    expect(screen.getByText(/Job Management/i)).toBeInTheDocument();
  });

  test("navigates to settings page when settings link is clicked", async () => {
    const user = userEvent.setup();
    render(<App />);

    const settingsLink = screen.getByRole("link", { name: /Settings/i });
    await user.click(settingsLink);

    // SettingsPage should be visible
    expect(screen.getByText(/Settings/i)).toBeInTheDocument();
  });

  test("renders footer with phase information", () => {
    render(<App />);

    const footer = screen.getByText(/Faza 2: Electron/i);
    expect(footer).toBeInTheDocument();
  });

  test("maintains navigation bar on all routes", async () => {
    const user = userEvent.setup();
    render(<App />);

    // Navigation should be visible on dashboard
    expect(screen.getByText("ADRIAN 369")).toBeInTheDocument();

    // Navigate to jobs
    await user.click(screen.getByRole("link", { name: /Jobs/i }));
    expect(screen.getByText("ADRIAN 369")).toBeInTheDocument();

    // Navigate to settings
    await user.click(screen.getByRole("link", { name: /Settings/i }));
    expect(screen.getByText("ADRIAN 369")).toBeInTheDocument();
  });

  test("handles rapid navigation between routes", async () => {
    const user = userEvent.setup();
    render(<App />);

    // Rapid navigation
    await user.click(screen.getByRole("link", { name: /Jobs/i }));
    await user.click(screen.getByRole("link", { name: /Settings/i }));
    await user.click(screen.getByRole("link", { name: /Dashboard/i }));
    await user.click(screen.getByRole("link", { name: /Jobs/i }));

    // Should end up on jobs page
    expect(screen.getByText(/Job Management/i)).toBeInTheDocument();
  });
});
