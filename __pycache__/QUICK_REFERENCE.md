# Quick Reference Card - Bid Checking Feature

## 🎯 What's New?

You can now **mark bids as "checked"** to avoid reviewing them repeatedly!

## 🚀 Quick Start (3 Steps)

1. **After analysis loads**, select bid(s) from the dropdown
2. **Click "Mark as Checked"** → They turn YELLOW with ✅
3. **Next day**, those bids stay yellow - focus on white ones!

## 🎨 Visual Guide

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| Checked | ✅ | Yellow Background | You've reviewed this |
| Unchecked | ⬜ | White Background | Needs your review |

## 🔧 Key Features

### Marking Bids
```
1. Select from dropdown → "Mark as Checked" → Done!
2. Or: "Mark All Visible as Checked" (bulk operation)
```

### Filtering
```
Filter 1: Keyword Group → Traction Batteries, Plante, etc.
Filter 2: Check Status → All / Checked Only / Unchecked Only
```

### Common Workflows

**Focus on New Bids:**
1. Set filter to "Unchecked Only"
2. Review white rows
3. Mark irrelevant ones

**Category Completion:**
1. Pick a Keyword Group
2. Filter to "Unchecked Only"  
3. Mark all when done
4. Move to next group

**Bulk Operations:**
1. Filter as needed
2. "Mark All Visible" → Instantly mark everything shown

## 📊 Progress Tracking

**Top Metrics:**
- Total Bids, Checked, Unchecked, Completion %

**Bottom Table:**
- Per-category completion breakdown

## 💾 Downloads

- **Filtered Data**: Current view
- **Checked Bids**: All reviewed bids
- **Unchecked Bids**: All pending bids

## 🔄 Daily Routine

```
Monday:
  Run scraper → Analyze → Mark irrelevant bids → DONE

Tuesday:
  Run scraper → Analyze → See yesterday's yellow → Review only white → DONE

Wednesday+:
  Repeat → Watch completion % grow!
```

## ⚠️ Important Notes

- ✅ Check status is PERMANENT (saved in `checked_bids.json`)
- ✅ Doesn't affect scraping logic
- ✅ Can unmark if needed
- ✅ Works offline, no database needed

## 🆘 Quick Fixes

**Reset everything:** Delete `data/checked_bids.json`
**Undo a mark:** Select bid → "Unmark Selected"
**See what's left:** Filter to "Unchecked Only"

---

**File Storage:** `data/checked_bids.json`
**Format:** Simple JSON dictionary
**Persistence:** Forever (until you delete it)
