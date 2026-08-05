import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import Dashboard from "./Dashboard";
import * as useApiModule from "../hooks/useApi";

// Mock the useApi hook
vi.mock("../hooks/useApi", () => ({
  useApi: vi.fn(),
}));

describe("TaxiDashboard", () => {
  it("renders loading states or placeholders when data is null", () => {
    // Mock all API hooks to return null data (loading state)
    vi.spyOn(useApiModule, "useApi").mockReturnValue({
      data: null,
      error: null,
      loading: true,
      refetch: vi.fn(),
    });

    render(<Dashboard />);

    // Assert main header renders
    expect(screen.getByText("Fleet Analytics Dashboard")).toBeInTheDocument();
    
    // Check that loading placeholders ("…") appear in cards
    const loaders = screen.getAllByText("…");
    expect(loaders.length).toBeGreaterThan(0);
  });

  it("renders dashboard cards and charts when data is successfully loaded", () => {
    vi.spyOn(useApiModule, "useApi").mockImplementation((url: string) => {
      if (url === "/api/stats") {
        return { data: { rows: 1500, avg_fare: 24.5 }, error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/tip-stats") {
        return { data: { avg_tip: 4.2, avg_tip_pct: 0.18 }, error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/duration-stats") {
        return { data: { avg: 650 }, error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/fraud-signals") {
        return { data: { cash_only: 320, zero_distance_nonzero_fare: 12 }, error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/hourly-distribution") {
        return { data: [{ hour: 10, count: 45 }], error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/payment-types") {
        return { data: { Credit: 800, Cash: 200 }, error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/revenue-velocity") {
        return { data: [{ hour: 10, avg_earnings_per_hour: 55.2, avg_earnings_per_mile: 12.4 }], error: null, loading: false, refetch: vi.fn() };
      }
      if (url === "/api/tolls-and-surcharges") {
        return {
          data: {
            tolls: { total: 1250.0, average: 2.5 },
            improvement_surcharge: { total: 500.0, average: 1.0 },
            congestion_surcharge: { total: 800.0, average: 2.0 },
          },
          error: null,
          loading: false,
          refetch: vi.fn(),
        };
      }
      return { data: null, error: null, loading: false, refetch: vi.fn() };
    });

    render(<Dashboard />);

    // Assert that populated values are rendered correctly
    expect(screen.getByText("24.50")).toBeInTheDocument(); // Avg. Fare
    expect(screen.getByText("1,500")).toBeInTheDocument(); // Trips Processed
    expect(screen.getByText("1,250.00")).toBeInTheDocument(); // Total Tolls
    expect(screen.getByText("Revenue Velocity (Earnings per Hour)")).toBeInTheDocument();
  });
});
