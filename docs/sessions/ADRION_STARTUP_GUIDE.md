# Quick Start: ADRION 369 Control Center

## Opening the Dashboard

**Option 1: Direct File Opening**

```bash
# Windows
start "" "file:///c:/Users/adiha/162 demencje w schemacie 369/adrion_control_center.html"

# Or paste in browser address bar:
file:///c:/Users/adiha/162 demencje w schemacie 369/adrion_control_center.html
```

**Option 2: Python Web Server (Recommended)**

```bash
cd "c:\Users\adiha\162 demencje w schemacie 369"

# Start simple HTTP server
python -m http.server 8000

# Open in browser:
http://localhost:8000/adrion_control_center.html
```

---

## Testing the Dashboard

### Prerequisites

- All 6 MCP agents running (Router, Guardian, Healer, Genesis, Oracle, Vortex)
- Ports 9001-9006 accessible
- Browser with modern JavaScript support

### Step 1: Start Agents

```bash
cd "c:\Users\adiha\162 demencje w schemacie 369"
python quick_start_agents.py
```

Expected output:

```
[START] Router (port 9001)
[START] Guardian (port 9002)
[START] Healer (port 9003)
[START] Genesis (port 9004)
[START] Oracle (port 9005)
[START] Vortex (port 9006)

[OK] All 6 agents started
Status:
Agents online: 6/6

Ready for testing!
```

### Step 2: Open Dashboard

```bash
# Open in any browser (Chrome, Edge, Firefox)
http://localhost:8000/adrion_control_center.html
```

You should see:

- ✅ 6 green agent cards (all online)
- ✅ KPI showing 6/6 agents online
- ✅ Live console with startup messages
- ✅ API Test Console ready to use

### Step 3: Test API Endpoints

**Test 1: Health Check (Router)**

1. Click "Router" agent card
2. Verify endpoint: `http://localhost:9001/health`
3. Click "Send Request"
4. Check console for: `[200] Router responding`

**Test 2: Test Another Agent**

1. Click "Genesis" agent card
2. Endpoint auto-updates: `http://localhost:9004/health`
3. Send request
4. Should see successful health response

**Test 3: Custom Endpoint**

1. Manually edit endpoint field
2. Example: `http://localhost:9001/status`
3. Change method to GET (if needed)
4. Send and verify response

**Test 4: Error Handling**

1. Enter invalid endpoint: `http://localhost:9999/health`
2. Click Send
3. Should show error in console: `[ERROR] Connection refused`

---

## UI Features Demo

### Agent Selection

- **Click any agent card** → Endpoint updates automatically
- **Green dot** = Agent online
- **Red dot** = Agent offline

### API Testing

- **Method Selector:** GET, POST, PUT, DELETE
- **Endpoint Input:** Type any URL
- **Send Button:** Orange gradient with hover effect
- **Response Display:** Appears in Live Console

### Live Console

- **Color-coded output:**
  - 🟢 **Green:** Success messages
  - 🔴 **Red:** Errors
  - 🟡 **Yellow:** Warnings
  - 🔵 **Blue:** Info
- **Auto-scroll:** Console follows latest entries
- **Timestamps:** Every log has HH:MM:SS

### KPI Metrics

- **6/6 Online:** Current agent status
- **100% Uptime:** System reliability
- **46 Tests:** Completed API tests from earlier sessions

### Tools Configuration

- **Read Files:** Check to allow file access
- **Execute Code:** Check to allow code execution
- **Internet Access:** Check to allow external connections
- **Database Query:** Check to allow DB operations

---

## Console Commands (Via Browser DevTools)

If you want to manually trigger functions:

```javascript
// Test API
testAPI();

// Add log message
addConsoleLog("Custom message", "success");

// Select agent
selectAgent("Guardian", 9002);

// Update endpoint
document.getElementById("endpointInput").value = "http://localhost:9003/health";
```

---

## Troubleshooting

### Issue: Agents show as offline

**Solution:**

1. Verify agents are running: `python quick_start_agents.py`
2. Check ports are listening: `netstat -an | findstr LISTEN`
3. Reload dashboard in browser

### Issue: API requests timeout

**Solution:**

1. Check endpoint URL is correct
2. Verify agent is responding to curl: `curl http://localhost:9001/health`
3. Check firewall settings

### Issue: Console not showing output

**Solution:**

1. Open browser DevTools (F12)
2. Check Console tab for JavaScript errors
3. Try refreshing page

### Issue: Dark mode looks broken

**Solution:**

1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Try different browser

---

## Performance Tips

- **Auto-refresh:** Health checks happen every 30 seconds (configurable)
- **Local Storage:** (Future) Settings saved to browser
- **WebSocket:** (Future) Real-time updates without polling

---

## Browser Compatibility

- ✅ Chrome 90+
- ✅ Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ⚠️ IE11 not supported (uses modern CSS Grid)

---

## Keyboard Shortcuts (Planned)

- `Ctrl+1` - Select Router
- `Ctrl+2` - Select Guardian
- `Ctrl+3` - Select Healer
- `Ctrl+4` - Select Genesis
- `Ctrl+5` - Select Oracle
- `Ctrl+6` - Select Vortex
- `Enter` - Send API request
- `Ctrl+L` - Clear console

---

## Files Included

| File                              | Purpose                          |
| --------------------------------- | -------------------------------- |
| `adrion_control_center.html`      | Main dashboard (open in browser) |
| `ADRION_CONTROL_CENTER_README.md` | Feature documentation            |
| `ADRION_STARTUP_GUIDE.md`         | This file (quick start)          |

---

## Next Session

1. **Enable WebSocket**
   - Real-time agent status
   - Live log streaming
   - No polling needed

2. **Add More Endpoints**
   - Test all 46 API endpoints
   - Performance metrics graph
   - Request history browser

3. **Save Settings**
   - Remember selected agent
   - Save tool preferences
   - Store API history

4. **Mobile App**
   - React Native companion app
   - Remote agent monitoring
   - Push notifications

---

**Created:** 2026-04-08
**Status:** Ready to Use
**Requirements:** Python 3.11 + Agents Running
