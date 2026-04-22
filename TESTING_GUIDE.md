# 🧪 Library Management System - Quick Testing Guide

## Getting Started

### 1. Start the Development Server
```bash
cd c:\library_management
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000/

---

## Test Scenarios

### Scenario 1: Browse & Search Books
1. Navigate to **Catalog** → `/catalog/`
2. Notice the filtering options:
   - Search box (search by title, author, ISBN)
   - Price range filters (min/max price)
   - Rating filter (minimum review rating)
   - Sorting options (price, rating, newest)
3. Try different combinations to filter books
4. View search results at `/catalog/search/`

**Expected Result:** Books list updates with applied filters

---

### Scenario 2: Add & Manage Reviews
1. Click on any **Book Title** to view details
2. Scroll to **"Avis des lecteurs"** section
3. **First time viewing:**
   - Click **"Laisser un avis"** button
   - Select 1-5 star rating
   - Type your review comment
   - Click **"Publier l'Avis"**
4. **After publishing:**
   - Your review appears in the section
   - Book's average rating updates
   - Click **"Modifier votre avis"** to edit
   - Use dropdown menu to **Delete** your review

**Expected Result:** 
- Review appears immediately
- Book rating recalculates
- Review count increments

---

### Scenario 3: View User Dashboard
1. Click **User Menu** (top right) → **Mon Compte**
2. View comprehensive dashboard with:
   - **Emprunts** section: Active, overdue, total counts
   - **Commandes** section: Pending, delivered, total counts
   - **Réservations** section: Active count
   - **Avis** section: Total reviews published
   - **Recent Activity**: Last 5 borrows and orders

3. Click action buttons in dashboard:
   - View recent borrow details
   - View recent order details

**Expected Result:** All statistics display correctly with accurate counts

---

### Scenario 4: View Borrow Details  
1. From Dashboard, scroll to **Emprunts Récents** table
2. Click the **"Voir"** button on any borrow
3. View complete borrow information:
   - Book title and details
   - Borrow and due dates
   - Current status
   - Any associated fines
4. If borrow is active:
   - Click to **"Retourner le Livre"**
   - Optionally click to **"Renouveler l'Emprunt"**

**Expected Result:** Detailed borrow view loads correctly with action buttons

---

### Scenario 5: Test User Authentication
1. **Without login:**
   - Try to add a review → Redirected to login
   - Try to access dashboard → Redirected to login
   
2. **With login:**
   - Register new account or use existing admin account
   - All features become available
   - User-specific data displays (your reviews, orders, etc.)

**Expected Result:** Access control works properly

---

## Test Data Checklist

### Required Database Records
- [ ] At least 5 books in the catalog
- [ ] Books with different prices
- [ ] Books with varying review counts
- [ ] Your user account (at least one user)
- [ ] At least one order for the logged-in user
- [ ] At least one borrow for the logged-in user
- [ ] At least one review from the logged-in user

### Admin Interface (`/admin/`)
1. Go to http://127.0.0.1:8000/admin/
2. Login with superuser credentials
3. Verify you can add/edit:
   - Books
   - Reviews
   - Orders
   - Borrows

---

## Common Issues & Solutions

### Issue: Template not found
**Solution:** Check that all files are in correct locations:
- `templates/catalog/add_review.html` ✓
- `templates/catalog/search_results.html` ✓
- `templates/borrowing/borrow_detail.html` ✓

### Issue: Reviews not showing average rating
**Solution:** Ensure reviews exist for the book. Rating updates when reviews are added/deleted.

### Issue: Dashboard shows no statistics
**Solution:** 
- Verify you're logged in
- Check that database records exist for your user
- Run: `python manage.py shell` to verify data

### Issue: Search filters not working
**Solution:** 
- Ensure books have price and rating values
- Try simplifying filter criteria
- Check browser console for JavaScript errors

---

## Performance Testing

### Load Test Scenarios
1. **Search Performance:** Search with complex filters (all fields)
2. **Dashboard Loading:** Speed of dashboard with many recent items
3. **Review Rendering:** Page with many reviews (10+ per book)
4. **Concurrent Users:** Multiple users browsing simultaneously

### Optimization Tips
- Database indexing on search fields (title, author)
- Pagination for large result sets
- Cache frequently accessed book ratings

---

## Browser Compatibility
- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (responsive design)

---

## Manual Feature Walkthrough

### Book Discovery Flow
```
Visit /catalog/ 
→ Search or filter books 
→ Click on interesting book 
→ Read details and reviews 
→ Add your review 
→ Add to cart / Reserve / Borrow
```

### User Account Flow
```
Login / Register 
→ Click Mon Compte 
→ View comprehensive statistics 
→ Click on recent activity 
→ View detailed borrow/order pages
```

### Review Creation Flow
```
View book details 
→ Scroll to reviews section 
→ Click "Laisser un avis" 
→ Select rating and write comment 
→ Submit form 
→ Review appears on page
```

---

## Debugging Tips

### Enable Django Debug Mode
Edit `settings.py`:
```python
DEBUG = True
ALLOWED_HOSTS = ['*']
```

### Check Database
```bash
python manage.py dbshell
SELECT COUNT(*) FROM catalog_book;
SELECT COUNT(*) FROM catalog_review;
SELECT * FROM catalog_review LIMIT 5;
```

### Verify Template Rendering
Check browser Developer Tools → Elements tab for HTML structure

### Check Console Logs
```bash
# Terminal where runserver is running shows all requests/errors
```

---

## Next Steps After Testing

1. **Fix any issues found** during testing
2. **Add more test data** if needed
3. **Optimize performance** if slow areas identified
4. **Prepare for deployment** to production
5. **Document any deviations** from this guide

---

## Quick Command Reference

```bash
# Start server
python manage.py runserver

# Access admin
http://127.0.0.1:8000/admin/

# Access app
http://127.0.0.1:8000/

# Create data
python manage.py shell
>>> from apps.catalog.models import Book, Category, Author
>>> # Add test data here

# Check migrations
python manage.py showmigrations

# Reset database
python manage.py flush
python manage.py migrate
```

---

**Ready to test! 🚀**

Report any issues or features that need adjustment.
