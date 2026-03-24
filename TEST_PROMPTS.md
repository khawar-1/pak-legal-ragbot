# Test Prompts for AWS Cloud Architecture Planner Chatbot

## 🧪 Progressive Test Prompts (Step by Step)

### Step 1: Start Simple (First Message)
```
I want to build an e-commerce platform for selling electronics online.
```
**Expected:** Extract `project_type` only, then ask 2 follow-up questions (scalability, storage)

### Step 2: Answer Follow-ups (Second Message)
```
Expecting about 10,000 daily users that might grow to 100,000. We'll store product images and customer order data.
```
**Expected:** Extract `scalability` and `storage`, then ask next 2 questions (security, region)

### Step 3: Continue (Third Message)
```
Need user login, payment processing with secure encryption. Target region is US East Coast.
```
**Expected:** Extract `security` and `region`, then ask next 2 questions (compute, database)

### Step 4: Continue (Fourth Message)
```
Auto-scaling compute for traffic spikes. Using a relational database for orders and products.
```
**Expected:** Extract `compute` and `database`, then ask next 2 questions (networking, deployment_preferences)

### Step 5: Final (Fifth Message)
```
Need global CDN for fast image loading worldwide. Prefer serverless with Lambda functions.
```
**Expected:** Extract `networking` and `deployment_preferences`, then show completion with buttons!

---

## 🧪 Single Message Test (If System Stops)

**First Message** (Start Simple):
```
I want to create a video streaming platform
```

**Expected Behavior:**
- ✅ Extracts: project_type
- ✅ Asks: 2 follow-up questions about scalability and storage
- ❌ Should NOT stop - must continue asking

**Second Message** (Answer Partially):
```
Targeting 1 million users globally. We'll store videos and user profiles.
```

**Expected Behavior:**
- ✅ Extracts: scalability, storage
- ✅ Asks: Next 2 questions about security and region

**Continue this pattern** until all 9 fields are filled!

---

## 📋 Individual Field Test Prompts

### Test 1: Basic Project Start (Minimal Info)
```
I want to build a video streaming platform
```
**Expected:** Should extract only `project_type: "video streaming platform"` and ask follow-up questions for remaining 8 fields.

---

### Test 2: Check Strict Extraction (No Inference)
```
I want to create an online store for 50 users
```
**Expected:** Should extract:
- ✅ project_type: "online store"
- ✅ scalability: "50 users"
- ❌ Should NOT infer storage, security, compute, etc. automatically

---

### Test 3: Complete Information Test
```
I'm building a social media application called "ConnectHub" for connecting professionals. 
We expect about 5,000 active users initially, growing to 50,000 within 6 months. 
We'll store user profiles, posts, images, videos, and messages. 
The app needs OAuth authentication, SSL encryption, and GDPR compliance. 
We require serverless functions that scale automatically and handle real-time messaging. 
The primary region is Europe (eu-west-1) but we need global CDN for media files. 
We'll use a NoSQL database for flexible schema and document storage. 
We prefer container-based deployment with Kubernetes for orchestration.
```

**Expected:** All 9 fields should be extracted.

---

## 🔄 Update Requirements Test Prompt

### Step 1: Complete Requirements
Use the comprehensive prompt above to fill all 9 fields.

### Step 2: Click "Update Requirements" button

### Step 3: Update Specific Fields
```
I want to change the region to Asia-Pacific and update storage to include user-generated content videos
```
**Expected:** System should:
- Clear `region` and `storage` fields
- Re-ask questions for these 2 fields
- Keep other 7 fields intact

---

## 🎭 Question Rephrasing Test

### Test Retry 1: First Ask
User doesn't answer clearly when asked about storage.

### Test Retry 2: Second Ask (Simpler)
System should ask a simpler version.

### Test Retry 3: Third Ask (Very Simple)
System should ask a very simple version.

### Test Retry 4+: LLM Generation
System should generate a contextual, simplified question.

---

## 🧩 Edge Case Test Prompts

### Test 1: Overwhelming Information
```
I want to build a healthcare management system for a hospital network with 20 branches. 
Each branch serves around 500 patients daily. The system needs to store patient records, 
medical images (X-rays, MRIs), doctor notes, appointment schedules, billing information, 
and prescription data. We require HIPAA compliance, multi-factor authentication, 
role-based access control, encrypted data at rest and in transit. The compute needs to 
handle peak loads during morning hours with 1000+ concurrent users, real-time 
synchronization across all branches, and AI-powered diagnostic image analysis. 
Deploy in us-west-2 for primary and us-east-1 for disaster recovery. Use both relational 
database for structured data and NoSQL for flexible schemas. Implement global CDN for 
medical imaging files, VPC with private subnets, and load balancers. Prefer hybrid 
deployment with on-premises servers for sensitive data and cloud for less critical 
information using containers and orchestration.
```

**Expected:** Should extract all information but ask only 2 questions at a time.

---

### Test 2: Very Minimal Input
```
online shop
```
**Expected:** Should extract only project_type and ask follow-ups.

---

### Test 3: Partial Information
```
Building a blog website for 100 daily visitors. Need to store blog posts and images.
```
**Expected:**
- ✅ project_type: "blog website"
- ✅ scalability: "100 daily visitors"
- ✅ storage: "blog posts and images"
- Should ask for remaining 6 fields

---

## 🔀 Mode Switching Test

### Test Flow:
1. Start in Requirement Extraction mode
2. Fill 5 out of 9 requirements
3. Switch to AWS Chat mode
4. Ask: "What is AWS Lambda?"
5. Switch back to Requirement Extraction mode

**Expected:**
- ✅ Progress bar shows 5/9 completed
- ✅ Chat history preserved
- ✅ Missing fields list still visible

---

## ✅ Completion & Confirmation Test

### Test Flow:
1. Fill all 9 requirements
2. System shows "Requirement Extraction Successful!"
3. Click "View AWS Services"

**Expected:**
- ✅ Requirements marked as complete in MongoDB
- ✅ Confirmation message displayed
- ✅ is_complete = true in database

---

## 🔄 Update Cycle Test

### Test Flow:
1. Complete all requirements
2. Click "Update Requirements"
3. Specify: "Change region to worldwide and update database to NoSQL"
4. Answer re-asked questions
5. Complete requirements again
6. Click "View AWS Services"

**Expected:**
- ✅ Only `region` and `database` fields cleared
- ✅ Other 7 fields remain unchanged
- ✅ System asks questions only for cleared fields
- ✅ Can complete and confirm again

---

## 🚫 Strict Extraction Test (Should NOT Extract)

### Test Input:
```
I want to build a small e-commerce app, you know, the typical setup with basic features
```
**Expected:**
- ✅ project_type: "e-commerce app"
- ✅ scalability: "small"
- ❌ Should NOT extract "basic features" as specific requirements
- Should ask follow-up questions instead of inferring

---

## 🎯 Quick Test Scenarios for FYP Demo

### Scenario 1: E-commerce Platform (5 minutes)
```
I want to create an online store for selling fashion items. 
Expecting around 5,000 daily users. Need to store product images and customer data.
```

**Demo Points:**
- Progress tracking
- Follow-up questions
- Question rephrasing (if user doesn't answer)
- Completion and confirmation

### Scenario 2: Video Platform (3 minutes)
```
Building a YouTube-like video sharing platform for 1 million users globally.
```

**Demo Points:**
- Strict extraction (won't infer all requirements)
- Global CDN networking needs
- Large-scale compute requirements
- Region selection for worldwide deployment

### Scenario 3: Blog Website (2 minutes)
```
Simple blog website for 100 visitors. Need basic storage and security.
```

**Demo Points:**
- Minimal requirements
- Simple deployment preferences
- Basic security needs

---

## 📊 Test Checklist

- [ ] Basic extraction works (project type identified)
- [ ] Strict extraction (no inference)
- [ ] Follow-up questions appear (2 at a time)
- [ ] Progress bar updates correctly
- [ ] Question rephrasing works (3 variants)
- [ ] LLM-generated questions work (after 3 attempts)
- [ ] All 9 fields can be extracted
- [ ] Completion detection works
- [ ] "View AWS Services" button marks complete
- [ ] "Update Requirements" button works
- [ ] Update flow clears and re-asks correctly
- [ ] Mode switching preserves progress
- [ ] Session persistence across refresh
- [ ] MongoDB saves all data correctly
- [ ] RAG works in AWS Chat mode
- [ ] Loading indicators are mode-specific

---

## 💡 Tips for Testing

1. **Test strict extraction first** - Make sure system doesn't infer requirements
2. **Test question rephrasing** - Don't answer clearly to see progressive simplification
3. **Test update flow** - Complete requirements, then update specific fields
4. **Test mode switching** - Verify progress and history are preserved
5. **Test edge cases** - Minimal input, overwhelming input, unclear input
6. **Check MongoDB** - Verify data is saved correctly in database
7. **Test UI responsiveness** - Buttons, loading states, progress updates

---

## 🎬 Demo Script (Recommended)

1. **Start**: "I want to build an e-commerce platform"
2. **Answer follow-ups** until 3-4 fields filled
3. **Don't answer clearly** for one question → Show rephrasing
4. **Switch to AWS Chat** → Ask AWS question
5. **Switch back** → Show progress preserved
6. **Complete all requirements** → Show confirmation buttons
7. **Update requirements** → Show update flow
8. **Confirm** → Mark as complete

**Total Demo Time:** ~10-12 minutes

---

Last Updated: Current Implementation
Ready for Testing ✅

