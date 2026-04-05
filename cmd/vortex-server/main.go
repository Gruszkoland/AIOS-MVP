package main

import (
	"adrion-vortex/internal/api"
	"adrion-vortex/internal/quantum"
	"crypto/hmac"
	"fmt"
	"log"
	"os"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

// vortexAuthMiddleware enforces shared-secret auth via X-Vortex-Key header.
// If VORTEX_SECRET_KEY is empty (dev mode) all requests are passed through.
func vortexAuthMiddleware(secret string) echo.MiddlewareFunc {
	return func(next echo.HandlerFunc) echo.HandlerFunc {
		return func(c echo.Context) error {
			if secret == "" {
				return next(c) // dev mode — brak klucza = przepuszcza
			}
			key := c.Request().Header.Get("X-Vortex-Key")
			if !hmac.Equal([]byte(key), []byte(secret)) {
				return c.JSON(401, map[string]string{"error": "unauthorized"})
			}
			return next(c)
		}
	}
}

func main() {
	fmt.Println("ADRION 369 Vortex Engine v1.0.0")
	// Initialize Vortex Engine (3-6-9) and Oracle
	vortex := quantum.NewVortexNode()
	oracle := &quantum.OracleNode{Vortex: vortex}

	// Start 174Hz Oscillation Tracker
	vortex.StartOscillation(func(resonance int) {
		log.Printf("[VORTEX] resonance=%d health=%.2f", resonance, vortex.GetHealth())
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

	// CORS: env-configurable, defaults to dashboard origin (U-05)
	corsOrigin := os.Getenv("CORS_ALLOWED_ORIGIN")
	if corsOrigin == "" {
		corsOrigin = "http://localhost:8003"
	}
	e.Use(middleware.CORSWithConfig(middleware.CORSConfig{
		AllowOrigins: []string{corsOrigin},
		AllowMethods: []string{echo.GET, echo.POST, echo.OPTIONS},
	}))

	// ── Public Routes (no auth) ──
	e.GET("/health", h.HealthCheck)

	// ── Protected Routes (require X-Vortex-Key header) ──
	vortexSecret := os.Getenv("VORTEX_SECRET_KEY")
	protected := e.Group("", vortexAuthMiddleware(vortexSecret))

	// Core Routes
	protected.POST("/decide", h.PostDecide)
	protected.GET("/status", h.GetStatus)

	// Sentinel Routes
	protected.POST("/sentinel/scan", h.SentinelScan)
	protected.GET("/sentinel/threats", h.GetThreats)

	// Oracle Routes
	protected.POST("/oracle/predict", h.OraclePredict)

	// Port from env or 1740 (174Hz alignment)
	port := os.Getenv("VORTEX_PORT")
	if port == "" {
		port = "1740"
	}
	fmt.Printf("⚡ ADRION Sentinel Vortex Engine on :%s (174Hz aligned)\n", port)
	e.Logger.Fatal(e.Start(":" + port))
}
