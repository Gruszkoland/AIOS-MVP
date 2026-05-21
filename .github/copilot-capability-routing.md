# Copilot Capability Routing Map

## Cel
Routing po mozliwosciach, nie po twardych ID agentow.

## Capability -> Agent
- implementation_automation -> AWA
- monetization_pricing -> REV
- security_audit -> security-guard
- architecture_design -> adrion-architect
- productivity_refactor -> high-yield-dev
- n8n_workflows -> n8n-architect
- personas_registry -> ai-personas

## Regula fallback
Jesli capability nieznane:
1. Escalate do adrion-architect.
2. Oznacz anomaly: MISSING_CAPABILITY.
3. Zaproponuj nowy skill lub MCP.
