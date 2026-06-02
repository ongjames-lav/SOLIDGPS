# DevTools Inspection Guide for Seek Business

## Step-by-Step (Do this while screen sharing)

### 1. Open Seek Business
- Go to: `https://www.seekbusiness.com.au/businesses-for-sale`
- Press **F12** to open DevTools

### 2. Find Listing Cards
1. Click the **Element Picker** tool (top-left of DevTools, looks like a cursor in a box)
2. Hover over a **business listing** on the page
3. Click on it
4. Look at the HTML structure in the Elements panel

### 3. What to Look For

**Container Element** (wraps entire listing):
- Look for `<article>` tags
- Look for `<div>` with classes like:
  - `listing`
  - `result`
  - `card`
  - `search-result`
  - Or `data-testid` attributes

**Title Element**:
- Usually `<h3>` or `<h2>` or `<a>` with class:
  - `title`
  - `heading`
  - `name`

**Location**:
- Look for text containing state codes (NSW, VIC, QLD)
- Usually in a `<span>` or `<div>` near the title

**Price**:
- Look for `$` symbol
- Usually in format: `$XXX,XXX` or `Price: $XXX,XXX`

### 4. Copy the Class Names
Right-click on the element → Copy → Copy selector

### 5. Test in Console
Switch to Console tab and run:
```javascript
// Count listing cards
document.querySelectorAll('article').length

// Get first listing title
document.querySelector('article h3')?.textContent

// Find all prices
document.querySelectorAll('article').forEach(a => console.log(a.textContent.match(/\$[\d,]+/)))
```

## Quick Checklist
- [ ] Opened DevTools (F12)
- [ ] Found listing container element
- [ ] Noted container class name or tag
- [ ] Found title element class
- [ ] Found location element
- [ ] Found price element
- [ ] Tested selectors in Console
