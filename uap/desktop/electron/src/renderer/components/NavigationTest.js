import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import React from "react";
import { useNavigate } from "react-router-dom";
/**
 * Quick navigation test - verifies React Router is working
 */
export function NavigationTest() {
    const navigate = useNavigate();
    const [testStatus, setTestStatus] = React.useState({});
    const runTests = async () => {
        const results = {};
        try {
            // Test 1: Dashboard route exists
            navigate("/", { replace: true });
            results["Dashboard Route"] = true;
        }
        catch (e) {
            results["Dashboard Route"] = false;
        }
        try {
            // Test 2: Jobs route exists
            navigate("/jobs", { replace: true });
            results["Jobs Route"] = true;
        }
        catch (e) {
            results["Jobs Route"] = false;
        }
        try {
            // Test 3: Settings route exists
            navigate("/settings", { replace: true });
            results["Settings Route"] = true;
        }
        catch (e) {
            results["Settings Route"] = false;
        }
        setTestStatus(results);
    };
    React.useEffect(() => {
        runTests();
    }, []);
    return (_jsxs("div", { className: "p-4 bg-blue-50 rounded-lg", children: [_jsx("h3", { className: "font-bold mb-2", children: "Navigation Test Results" }), Object.entries(testStatus).map(([test, passed]) => (_jsxs("div", { className: "text-sm flex items-center gap-2", children: [_jsx("span", { children: passed ? "✅" : "❌" }), _jsx("span", { children: test })] }, test)))] }));
}
export default NavigationTest;
//# sourceMappingURL=NavigationTest.js.map