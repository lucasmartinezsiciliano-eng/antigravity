# VISAI Testing Guide

**Status:** ⏳ Implementation in progress  
**Target:** May 16-17, 2026  
**Requirements:** pytest, pytest-asyncio, httpx

---

## Test Suite Overview

### Backend Tests (✅ Created)
- **Unit tests:** Service functions, database operations
- **API tests:** Endpoint validation, request/response contracts
- **Integration tests:** End-to-end flows, database transactions
- **Background jobs:** Leaderboard, photo approval, Telegram notifications

### Frontend Tests (⏳ Manual for MVP)
- **Component testing:** Modal, pages, form validation
- **E2E testing:** Full user flows (upload, leaderboard, parental consent)
- **Mobile responsiveness:** iPhone/Android viewport testing

---

## Running Backend Tests

### Setup

```bash
cd stylescan/backend

# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Verify installation
pytest --version
```

### Run all tests

```bash
pytest tests/ -v --tb=short
```

### Run specific test file

```bash
# Leaderboard API tests
pytest tests/test_leaderboard_api.py -v

# Reference photos tests
pytest tests/test_reference_photos_api.py -v

# Parental consent tests
pytest tests/test_parental_consent_api.py -v

# Background jobs tests
pytest tests/test_background_jobs.py -v
```

### Run with coverage report

```bash
pytest tests/ --cov=app --cov-report=html
# Opens: htmlcov/index.html
```

### Run single test

```bash
pytest tests/test_leaderboard_api.py::test_get_leaderboard_empty -v
```

---

## Test Files

| File | Purpose | Status |
|------|---------|--------|
| `tests/conftest.py` | Fixtures (test DB, sample data) | ✅ |
| `tests/test_leaderboard_api.py` | Leaderboard endpoints | ✅ |
| `tests/test_reference_photos_api.py` | Photo upload endpoints | ✅ |
| `tests/test_parental_consent_api.py` | Consent flow endpoints | ✅ |
| `tests/test_background_jobs.py` | Job execution tests | ✅ |

---

## Test Checklist

### Unit Tests (Automated)

- [ ] Leaderboard API
  - [ ] GET /leaderboard (empty, with data)
  - [ ] GET /leaderboard/stats/{id}
  - [ ] Period filters (week, month, all_time)
  - [ ] City filters
  - [ ] Pagination (limit, offset)

- [ ] Reference Photos API
  - [ ] GET /barbers/{id}/reference-photos (empty, with filters)
  - [ ] POST /barbers/{id}/reference-photos (file upload)
  - [ ] DELETE /barbers/{id}/reference-photos/{photo_id}
  - [ ] Validation (file format, size)

- [ ] Parental Consent API
  - [ ] POST /parental-consent/request (minor, adult, invalid email)
  - [ ] GET /parental-consent/authorize (valid token, expired, invalid)
  - [ ] GET /parental-consent/{token}/status
  - [ ] Token expiry (72 hours)

- [ ] Background Jobs
  - [ ] Leaderboard ranking recalculation
  - [ ] Tier badge assignment (Platinum/Gold/Silver/Bronze)
  - [ ] Photo auto-approval (quality >= 0.80)
  - [ ] Low-quality photo handling (manual review)

### Integration Tests (Manual)

#### Frontend - Barber Dashboard Flow

```
1. User logs in → Barber dashboard loads
   ✓ Dashboard loads metrics (week/month/all-time clients)
   ✓ Tier badge displays (Platinum/Gold/Silver/Bronze)
   ✓ Promo code visible + copy button works
   ✓ Reference photos gallery loads

2. User clicks "Upload Photo"
   ✓ Modal opens with 3 steps
   ✓ Haircut type selector works
   ✓ Photo angle selector works
   ✓ File picker accepts images only

3. User uploads frontal photo
   ✓ File uploads to Cloudinary
   ✓ MediaPipe analysis runs
   ✓ Quality score displays
   ✓ Photo appears in gallery

4. Dashboard reloads
   ✓ Reference photos count updates
   ✓ New photo visible in gallery
```

#### Frontend - Leaderboard Flow

```
1. User navigates to /barber/leaderboard
   ✓ Top 50 barberos load
   ✓ Tier badges visible
   ✓ Instagram handles link correctly

2. User filters by period
   ✓ "Esta Semana" shows week ranking
   ✓ "Este Mes" shows month ranking
   ✓ "Total" shows all-time ranking

3. User filters by city
   ✓ City dropdown auto-populated
   ✓ Filter updates leaderboard
   ✓ Results show only selected city

4. User searches by name
   ✓ Search input works
   ✓ Results filter in real-time
   ✓ Handles partial matches
```

#### Frontend - Parental Consent Flow

```
1. Minor (<18) submits analysis
   ✓ Parental consent request created
   ✓ Email sent to parent_email
   ✓ Token valid for 72 hours

2. Parent clicks authorization link
   ✓ Link opens /parental-consent/authorize?token=XXX
   ✓ Page shows loading state
   ✓ Authorization confirmed (green checkmark)
   ✓ Shows expiry date

3. Expired token scenario
   ✓ Old link shows "Link expirado"
   ✓ Shows orange warning
   ✓ Suggests requesting new link

4. Invalid token scenario
   ✓ Malformed token shows error
   ✓ Red alert displayed
   ✓ "Volver al Inicio" button visible
```

#### Backend - API Integration

```
1. POST /parental-consent/request
   ✓ Creates ParentalConsentRequest in DB
   ✓ Email sent via Resend
   ✓ Returns authorization_url
   ✓ Token is cryptographically unique

2. GET /parental-consent/authorize?token=XXX
   ✓ Validates token format
   ✓ Checks token not expired
   ✓ Updates is_authorized flag
   ✓ Returns correct status

3. GET /api/v1/leaderboard
   ✓ Returns top 50 by period
   ✓ Sorted by correct metric (clients_this_week, etc)
   ✓ Includes ranking position
   ✓ Includes tier badge

4. Background job: Leaderboard recalculation
   ✓ Runs daily at 03:00 UTC
   ✓ Updates ranking positions
   ✓ Assigns tier badges
   ✓ Logs execution
```

---

## Mobile Responsiveness Testing

### Devices to Test

- [ ] iPhone SE (375px width)
- [ ] iPhone 12/13 (390px width)
- [ ] iPhone 14 Pro Max (430px width)
- [ ] Android Samsung Galaxy S21 (360px width)
- [ ] iPad (768px width)

### Pages to Test

1. **Dashboard Page** (`/barber/dashboard?id=xxx`)
   - [ ] Metrics cards stack vertically on mobile
   - [ ] Reference photo gallery responsive
   - [ ] Modal opens correctly on small screens
   - [ ] File upload works on mobile

2. **Leaderboard Page** (`/barber/leaderboard`)
   - [ ] Search input visible
   - [ ] Filters accessible on mobile
   - [ ] Leaderboard entries don't overflow
   - [ ] Instagram link works
   - [ ] Touch targets large enough (44px min)

3. **Parental Consent Page** (`/parental-consent/authorize`)
   - [ ] All states render correctly
   - [ ] Text readable at 375px
   - [ ] CTA buttons full-width
   - [ ] No horizontal scrolling

### Testing Tools

```bash
# Chrome DevTools mobile emulation
# Responsive Design Mode (Ctrl+Shift+M)
# Test with actual devices if available
```

---

## Known Limitations (MVP)

### Backend Testing
- ❌ No Cloudinary integration test (uses mock)
- ❌ No Telegram webhook testing (requires bot token)
- ❌ No MediaPipe integration test (requires library setup)
- ❌ No Resend email testing (requires API key)

### Frontend Testing
- ❌ No E2E test automation (manual testing only)
- ❌ No Playwright/Cypress setup (can be added Week 2)
- ❌ No visual regression testing (manual screenshots)
- ❌ No accessibility testing (WCAG compliance)

### Deferred to Week 2
- Performance testing (load testing, response times)
- Security testing (OWASP Top 10 validation)
- API rate limiting tests
- Concurrent request handling

---

## Test Execution

### Pre-Launch Testing Schedule

**May 16 (Day 1): Unit Tests**
```
Morning (9:00 AM):
  - Run full test suite
  - Fix any failures
  - Verify all tests pass

Afternoon (2:00 PM):
  - Coverage report generation
  - Ensure coverage > 80%
```

**May 17 (Day 2): Integration Tests**
```
Morning (9:00 AM):
  - Manual backend flow testing
  - Database transaction validation
  - Error handling scenarios

Afternoon (2:00 PM):
  - Frontend manual testing
  - Mobile responsiveness checks
  - Cross-browser testing (Chrome, Firefox, Safari)
```

**May 18 (Day 3): Staging QA**
```
Full end-to-end testing:
  - All flows in staging environment
  - Real Cloudinary integration
  - Real email sending
  - Real Telegram notifications
```

---

## Running Tests Locally

### Full test run with output

```bash
# Verbose output
pytest tests/ -v --tb=short --capture=no

# Show print statements
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific tests matching pattern
pytest tests/ -k "leaderboard" -v
```

### Generate HTML report

```bash
pytest tests/ --html=report.html --self-contained-html
# Opens in browser: report.html
```

### Watch mode (auto-rerun on file change)

```bash
pip install pytest-watch
ptw tests/
```

---

## Debugging Tests

### Run test with debugger

```bash
# Set breakpoint in test
pytest tests/test_leaderboard_api.py::test_name --pdb

# Then use: l (list), n (next), c (continue), etc.
```

### Verbose logging

```python
# In test file
import logging
logging.basicConfig(level=logging.DEBUG)

# Run:
pytest tests/test_name.py -v -s --log-cli-level=DEBUG
```

---

## Continuous Integration (Week 2)

### GitHub Actions (optional)

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ --cov=app
```

---

## Success Criteria

✅ **Tests Pass:**
- All unit tests pass
- All integration tests pass
- Coverage > 80%
- No test timeouts

✅ **Manual Testing Complete:**
- Dashboard flow end-to-end
- Leaderboard filtering & search
- Parental consent email + authorization
- Mobile responsiveness verified
- No console errors in browser

✅ **Performance:**
- Dashboard loads < 1s
- Leaderboard loads < 2s
- Photo upload completes < 10s
- No memory leaks

---

**Generated:** 2026-05-16  
**Status:** Testing infrastructure ready  
**Next:** Execute test suite May 16-17
