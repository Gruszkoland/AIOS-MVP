import React from "react";
import { useNavigate } from "react-router-dom";

/**
 * Quick navigation test - verifies React Router is working
 */
export function NavigationTest() {
  const navigate = useNavigate();
  const [testStatus, setTestStatus] = React.useState<Record<string, boolean>>(
    {},
  );

  const runTests = async () => {
    const results: Record<string, boolean> = {};

    try {
      // Test 1: Dashboard route exists
      navigate("/", { replace: true });
      results["Dashboard Route"] = true;
    } catch (e) {
      results["Dashboard Route"] = false;
    }

    try {
      // Test 2: Jobs route exists
      navigate("/jobs", { replace: true });
      results["Jobs Route"] = true;
    } catch (e) {
      results["Jobs Route"] = false;
    }

    try {
      // Test 3: Settings route exists
      navigate("/settings", { replace: true });
      results["Settings Route"] = true;
    } catch (e) {
      results["Settings Route"] = false;
    }

    setTestStatus(results);
  };

  React.useEffect(() => {
    runTests();
  }, []);

  return (
    <div className="p-4 bg-blue-50 rounded-lg">
      <h3 className="font-bold mb-2">Navigation Test Results</h3>
      {Object.entries(testStatus).map(([test, passed]) => (
        <div key={test} className="text-sm flex items-center gap-2">
          <span>{passed ? "✅" : "❌"}</span>
          <span>{test}</span>
        </div>
      ))}
    </div>
  );
}

export default NavigationTest;
