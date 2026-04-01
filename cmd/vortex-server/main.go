package main

import (
	"adrion-vortex/internal/api"
	"adrion-vortex/internal/quantum"
	"fmt"
	"os"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

func main() {
	// Initialize Vortex Engine (3-6-9) and Oracle
	vortex := &quantum.VortexNode{}
	oracle := &quantum.OracleNode{Vortex: vortex}

	// Start 174Hz Oscillation Tracker
	vortex.StartOscillation(func(resonance int) {
		// Sentinel monitoring: resonance changes trigger scan evaluation
	})

	// Setup API Handler
	h := &api.Handler{Vortex: vortex, Oracle: oracle}

	// Echo Implementation
	e := echo.New()
	e.HideBanner = true

	// Middleware: Security Sentinel
	e.Use(middleware.LoggerWithConfig(middleware.LoggerConfig{
		Format: "[SENTINEL] ${time_rfc3339} ${method} ${uri} → ${status} (${latency_human})\n",
	}))
	e.Use(middleware.Recover())
	e.Use(middleware.CORSWithConfig(middleware.CORSConfig{
		AllowOrigins: []string{"*"},
		AllowMethods: []string{echo.GET, echo.POST, echo.OPTIONS},
	}))

	// ── Core Routes ──
	e.POST("/decide", h.PostDecide)
	e.GET("/status", h.GetStatus)

	// ── Sentinel Routes ──
	e.GET("/health", h.HealthCheck)
	e.POST("/sentinel/scan", h.SentinelScan)
	e.GET("/sentinel/threats", h.GetThreats)

	// ── Oracle Routes ──
	e.POST("/oracle/predict", h.OraclePredict)

	// Port from env or 1740 (174Hz alignment)
	port := os.Getenv("VORTEX_PORT")
	if port == "" {
		port = "1740"
	}
	fmt.Printf("⚡ ADRION Sentinel Vortex Engine on :%s (174Hz aligned)\n", port)
	e.Logger.Fatal(e.Start(":" + port))
}
