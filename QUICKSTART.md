# Quick Start Guide - CEO Execution OS

## Installation

```bash
# Clone repository
cd /home/theo/ceo-execution-os

# Install dependencies
pip install -e .

# Initialize database
python3 -m src.cli.main setup
```

## Daily Workflow

### Morning Check-in (60 seconds)

```bash
python3 -m src.cli.main daily checkin
```

**What it does:**
- Checks energy level
- Detects paralysis signals (tension/circular thinking)
- Sets today's ONE mission
- Forces definition of "done"
- Sets target completion time

**If paralysis detected:** System forces you to address it immediately.

### During the Day

Check your mission anytime:
```bash
python3 -m src.cli.main daily show
```

See overall status:
```bash
python3 -m src.cli.main status
```

### End of Day

Mark mission complete:
```bash
python3 -m src.cli.main daily complete --status shipped
```

Status options:
- `shipped` - Mission accomplished
- `blocked` - Couldn't complete
- `deferred` - Postponed

## Project Management

### Add a Project (Max 3 Active)

```bash
python3 -m src.cli.main project add "Launch MVP"
```

**Hard Cap:** You can only have 3 active projects. System will BLOCK you from adding more until you ship/kill one.

### List Projects

```bash
python3 -m src.cli.main project list
```

### Complete a Project

```bash
python3 -m src.cli.main project complete abc123
```

### Kill a Project

```bash
python3 -m src.cli.main project kill abc123
```

## When Paralyzed

### 20-Minute Decision Protocol

```bash
python3 -m src.cli.main daily decide
```

**What it does:**
- Blocks until you make a decision
- 4 steps: Externalize, Constraint, Simplify, Commit
- Forces communication (social commitment)
- Logs decision with timing

**This is BLOCKING** - you cannot exit without deciding.

## Circuit Breaker

### Check if Should Trigger

```bash
python3 -m src.cli.main emergency check
```

**Auto-triggers when:**
- 5+ paralysis episodes in 30 days
- Completion rate <60% for 2 consecutive weeks
- All projects stalled

### Manually Activate

```bash
python3 -m src.cli.main emergency activate
```

**What it does:**
- Forces focus on ONE project only
- Requires external accountability call
- Disables normal operations
- Simplified mode until recovery

### Deactivate

```bash
python3 -m src.cli.main emergency deactivate
```

Must have:
- Shipped 3+ things in 2 weeks
- Made 5+ decisions without paralysis
- External contact validation

## Key Features

### 1. Always-Visible Status

**Every command shows:**
- Today's mission status
- Weekly completion rate (shipped/total)
- Trend (improving ↑ or declining ↓)
- Color-coded: Green (>80%), Yellow (60-80%), Red (<60%)

### 2. Hard Constraints

- **3 project cap:** Cannot add more without shipping/killing one
- **Paralysis protocol:** Blocks CLI until addressed
- **Circuit breaker:** Auto-triggers, disables commands

### 3. Forcing Functions

- Mission requires "done" definition
- Paralysis requires immediate action
- Circuit breaker requires external call
- No escape hatches

## Data Location

```bash
~/.ceo-os/
├── data.db                    # SQLite database
└── .circuit_breaker_active    # Flag when CB active
```

**Database has 3 tables:**
- `daily_logs` - Check-ins and missions
- `projects` - Active projects (max 3)
- `decisions` - Decision timing log

## Metrics Calculated On-Demand

### Weekly Completion Rate

```sql
SELECT COUNT(CASE WHEN mission_status = 'shipped' THEN 1 END) * 100.0 / COUNT(*)
FROM daily_logs
WHERE date >= date('now', '-7 days');
```

### Paralysis Rate (30 days)

```sql
SELECT COUNT(CASE WHEN paralysis_signals = 1 THEN 1 END) * 100.0 / COUNT(*)
FROM daily_logs
WHERE date >= date('now', '-30 days');
```

## Backup

**Simple manual backup:**
```bash
cp ~/.ceo-os/data.db ~/Dropbox/ceo-backup-$(date +%Y%m%d).db
```

**Restore:**
```bash
cp ~/Dropbox/ceo-backup-20260114.db ~/.ceo-os/data.db
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_models.py -v

# Check coverage
pytest tests/ --cov=src --cov-report=html
```

## Development

### Project Structure

```
src/
├── cli/
│   ├── main.py          # Entry point + status header
│   ├── daily.py         # Daily check-in commands
│   ├── project.py       # Project management
│   └── emergency.py     # Circuit breaker
├── core/
│   ├── models.py        # 3 database tables
│   ├── database.py      # Connection + session
│   └── metrics.py       # SQL aggregations
└── protocols/
    ├── paralysis.py     # 20-min decision protocol
    └── circuit.py       # Circuit breaker logic
```

### Key Design Decisions

1. **No cloud sync** - Local SQLite, manual backup
2. **No ML/AI** - Simple SQL COUNT/AVG
3. **No notifications** - Use OS calendar
4. **No web dashboard** - CLI only
5. **Blocking protocols** - Cannot escape until completed

### Total LOC: ~1500 lines

- Models: ~120 lines
- Database: ~80 lines
- Metrics: ~180 lines
- CLI: ~600 lines
- Protocols: ~250 lines
- Tests: ~300 lines

## Troubleshooting

### Database locked error
```bash
# WAL mode should prevent this, but if it happens:
rm ~/.ceo-os/data.db-wal
rm ~/.ceo-os/data.db-shm
```

### Import errors
```bash
# Reinstall package
pip install -e .
```

### Tests failing
```bash
# Check Python version (3.8+ required)
python3 --version

# Reinstall dependencies
pip install -r requirements.txt
```

## What's Next?

After using daily for 2 weeks, consider adding:

1. **Export data** - CSV export for analysis
2. **Weekly reports** - Auto-generated summaries
3. **Cloud sync** - Encrypted backup (if needed)
4. **Advanced analytics** - Pattern detection
5. **Web dashboard** - Visualizations

But ship early with MVP first!

## Success Metrics

### You'll know it's working when:

- ✅ 90% daily check-in completion (21/30 days)
- ✅ Paralysis protocol used ≥3 times
- ✅ Circuit breaker triggers at least once
- ✅ Completion rate shows improving trend
- ✅ You report: "This actually helps"

### Red flags:

- ❌ Stopped using after 2 weeks
- ❌ Check-in takes >90 seconds
- ❌ Ignoring paralysis warnings
- ❌ Circuit breaker never triggers (not detecting)
- ❌ Still have 5+ active projects (cap not working)

## Support

- GitHub Issues: [Create issue](https://github.com/theomann/ceo-execution-os/issues)
- Documentation: See `/docs` folder
- Tests: See `/tests` folder

---

**Remember:** Done > Perfect. Ship early, iterate fast.
