//! OpenTelemetry Distributed Tracing — Phase 3-1
//! Provides trace context propagation, span creation, and correlation IDs
//! Enables end-to-end observability from decision kernel through consensus rounds

use std::fmt;

/// Trace context header (W3C format)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TraceContext {
    pub trace_id: u128,
    pub span_id: u64,
    pub parent_span_id: u64,
    pub trace_flags: u8, // sampled bit + other flags
}

impl TraceContext {
    pub fn new(trace_id: u128, span_id: u64) -> Self {
        TraceContext {
            trace_id,
            span_id,
            parent_span_id: 0,
            trace_flags: 0x01, // sampled
        }
    }

    pub fn with_parent(trace_id: u128, span_id: u64, parent_span_id: u64) -> Self {
        TraceContext {
            trace_id,
            span_id,
            parent_span_id,
            trace_flags: 0x01,
        }
    }

    pub fn is_sampled(&self) -> bool {
        (self.trace_flags & 0x01) != 0
    }

    /// W3C Traceparent format: traceparent: version-trace_id-parent_id-trace_flags
    pub fn to_traceparent(&self) -> String {
        format!(
            "00-{:032x}-{:016x}-{:02x}",
            self.trace_id, self.span_id, self.trace_flags
        )
    }

    pub fn from_traceparent(s: &str) -> Option<Self> {
        let parts: Vec<&str> = s.split('-').collect();
        if parts.len() != 4 || parts[0] != "00" {
            return None;
        }

        let trace_id = u128::from_str_radix(parts[1], 16).ok()?;
        let span_id = u64::from_str_radix(parts[2], 16).ok()?;
        let trace_flags = u8::from_str_radix(parts[3], 16).ok()?;

        Some(TraceContext {
            trace_id,
            span_id,
            parent_span_id: span_id,
            trace_flags,
        })
    }
}

impl fmt::Display for TraceContext {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "TraceContext(id={:032x}, span={:016x}, parent={:016x})",
            self.trace_id, self.span_id, self.parent_span_id
        )
    }
}

/// Span event for tracing
#[derive(Debug, Clone)]
pub struct SpanEvent {
    pub timestamp_nanos: u64,
    pub name: String,
    pub attributes: Vec<(String, String)>,
}

impl SpanEvent {
    pub fn new(timestamp_nanos: u64, name: String) -> Self {
        SpanEvent {
            timestamp_nanos,
            name,
            attributes: Vec::new(),
        }
    }

    pub fn with_attribute(mut self, key: String, value: String) -> Self {
        self.attributes.push((key, value));
        self
    }
}

/// Distributed span for tracing decision flow
#[derive(Debug, Clone)]
pub struct DistributedSpan {
    pub trace_context: TraceContext,
    pub name: String,
    pub start_nanos: u64,
    pub end_nanos: u64,
    pub events: Vec<SpanEvent>,
    pub status: SpanStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SpanStatus {
    Unset,
    Ok,
    Error,
}

impl DistributedSpan {
    pub fn new(trace_context: TraceContext, name: String, start_nanos: u64) -> Self {
        DistributedSpan {
            trace_context,
            name,
            start_nanos,
            end_nanos: 0,
            events: Vec::new(),
            status: SpanStatus::Unset,
        }
    }

    pub fn end(&mut self, end_nanos: u64) -> u64 {
        self.end_nanos = end_nanos;
        end_nanos - self.start_nanos
    }

    pub fn duration_nanos(&self) -> u64 {
        if self.end_nanos == 0 {
            0
        } else {
            self.end_nanos - self.start_nanos
        }
    }

    pub fn add_event(&mut self, event: SpanEvent) {
        self.events.push(event);
    }

    pub fn set_status(&mut self, status: SpanStatus) {
        self.status = status;
    }
}

/// Trace collector for all spans in a decision flow
pub struct TraceCollector {
    spans: Vec<DistributedSpan>,
    root_trace_id: u128,
}

impl TraceCollector {
    pub fn new(root_trace_id: u128) -> Self {
        TraceCollector {
            spans: Vec::new(),
            root_trace_id,
        }
    }

    pub fn add_span(&mut self, span: DistributedSpan) {
        self.spans.push(span);
    }

    pub fn spans(&self) -> &[DistributedSpan] {
        &self.spans
    }

    pub fn total_duration_nanos(&self) -> u64 {
        if self.spans.is_empty() {
            return 0;
        }

        let min_start = self.spans.iter().map(|s| s.start_nanos).min().unwrap_or(0);
        let max_end = self
            .spans
            .iter()
            .map(|s| if s.end_nanos == 0 { s.start_nanos } else { s.end_nanos })
            .max()
            .unwrap_or(0);

        max_end.saturating_sub(min_start)
    }

    pub fn span_count(&self) -> usize {
        self.spans.len()
    }

    pub fn export_json(&self) -> String {
        // Simple JSON export (production: use OpenTelemetry SDK)
        format!(
            r#"{{"trace_id":"{:032x}","span_count":{},"total_duration_ns":"{}"}}"#,
            self.root_trace_id,
            self.span_count(),
            self.total_duration_nanos()
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_trace_context_creation() {
        let ctx = TraceContext::new(0x12345678_abcdef01_abcdef01_abcdef01, 0x1234567890abcdef);
        assert_eq!(ctx.span_id, 0x1234567890abcdef);
        assert!(ctx.is_sampled());
    }

    #[test]
    fn test_traceparent_format() {
        let ctx = TraceContext::new(0x12345678_abcdef01_abcdef01_abcdef01, 0x1234567890abcdef);
        let traceparent = ctx.to_traceparent();
        assert!(traceparent.starts_with("00-"));
        assert!(traceparent.len() > 10);
    }

    #[test]
    fn test_traceparent_parse() {
        let original = TraceContext::new(0xffffffff_ffffffff_ffffffff_ffffffff, 0xffffffffffffffff);
        let traceparent = original.to_traceparent();
        let parsed = TraceContext::from_traceparent(&traceparent).unwrap();
        assert_eq!(parsed.trace_id, original.trace_id);
        assert_eq!(parsed.span_id, original.span_id);
    }

    #[test]
    fn test_distributed_span() {
        let ctx = TraceContext::new(1, 1);
        let mut span = DistributedSpan::new(ctx, "test_span".to_string(), 1000);
        assert_eq!(span.duration_nanos(), 0);

        span.end(2000);
        assert_eq!(span.duration_nanos(), 1000);
        assert_eq!(span.status, SpanStatus::Unset);
    }

    #[test]
    fn test_span_events() {
        let ctx = TraceContext::new(1, 1);
        let mut span = DistributedSpan::new(ctx, "span_with_events".to_string(), 1000);

        let event = SpanEvent::new(1100, "event1".to_string())
            .with_attribute("key".to_string(), "value".to_string());
        span.add_event(event);

        assert_eq!(span.events.len(), 1);
        assert_eq!(span.events[0].attributes[0].0, "key");
    }

    #[test]
    fn test_trace_collector() {
        let mut collector = TraceCollector::new(0x12345678_abcdef01_abcdef01_abcdef01);

        let ctx = TraceContext::new(0x12345678_abcdef01_abcdef01_abcdef01, 1);
        let mut span1 = DistributedSpan::new(ctx, "span1".to_string(), 1000);
        span1.end(2000);

        let mut span2 = DistributedSpan::new(ctx, "span2".to_string(), 2100);
        span2.end(3000);

        collector.add_span(span1);
        collector.add_span(span2);

        assert_eq!(collector.span_count(), 2);
        assert!(collector.total_duration_nanos() > 0);
    }

    #[test]
    fn test_trace_collector_json_export() {
        let mut collector = TraceCollector::new(0xaabbccdd_eeffaabb_ccddee00_11223344);
        let ctx = TraceContext::new(0xaabbccdd_eeffaabb_ccddee00_11223344, 1);
        let mut span = DistributedSpan::new(ctx, "test".to_string(), 1000);
        span.end(2500);

        collector.add_span(span);
        let json = collector.export_json();
        assert!(json.contains("aabbccddeeffaabbccdddee0011223344"));
        assert!(json.contains("\"span_count\":1"));
    }

    #[test]
    fn test_span_status() {
        let ctx = TraceContext::new(1, 1);
        let mut span = DistributedSpan::new(ctx, "test".to_string(), 1000);

        span.set_status(SpanStatus::Ok);
        assert_eq!(span.status, SpanStatus::Ok);

        span.set_status(SpanStatus::Error);
        assert_eq!(span.status, SpanStatus::Error);
    }
}
