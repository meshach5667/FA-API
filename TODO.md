# FitAccess MVP - Fix Todo List

## 1. API Issues
- [ ] Fix PUT /business-auth/profile endpoint (422 Unprocessable Entity error)
- [ ] Fix member payment status change (paid -> active, not inactive)

## 2. Analytics Dashboard Fixes
- [ ] Remove Monthly Trends from analytics
- [ ] Remove Member Growth from analytics  
- [ ] Remove Popular Activities from analytics
- [ ] Replace Popular Activities with real data component
- [ ] Fix member growth to use real-time data
- [ ] Fix total revenue to show actual sum of paid transactions

## 3. Transaction System Fixes
- [ ] Make transaction history show only transactions paid by members
- [ ] Fix transactions to show real paid transactions (not 0)
- [ ] Fix monthly revenue calculation to sum up actual paid transactions
- [ ] Remove "pending" status from transactions
- [ ] Ensure all transaction displays show real data

## 4. Business Profile
- [ ] Fix business profile image upload functionality
- [ ] Make uploaded image persist and not disappear until changed

## 5. Check-in/Check-out System
- [ ] Replace mock data with real data for check-in
- [ ] Replace mock data with real data for check-out  
- [ ] Implement functioning QR code for check-in
- [ ] Ensure QR code scanning works properly

## 6. Activity Management UI
- [ ] Fix UI for editing activities
- [ ] Ensure all activity fields are visible and editable
- [ ] Make sure editing form works properly

## 7. Member Management
- [ ] Fix member status change logic (paid -> active)
- [ ] Ensure member status updates correctly in UI

## Priority Order:
1. API endpoint fixes
2. Transaction system (core functionality)
3. Analytics with real data
4. Member status management
5. Business profile image upload
6. Check-in/out system with QR codes
7. Activity editing UI

## Status: 
- [ ] Complete all items
- [ ] Test entire system
- [ ] Verify all changes work together
