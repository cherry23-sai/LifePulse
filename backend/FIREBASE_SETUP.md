# LifePulse — Firebase Firestore setup

## Architecture
React → Django REST API → Firebase Admin SDK → Cloud Firestore
Memory files → Firebase Storage

MySQL is no longer used.

## 1. Create Firebase project
1. Open Firebase Console.
2. Create/select your LifePulse project.
3. Enable **Cloud Firestore**.
4. Enable **Storage**.
5. Create a Firestore database in a suitable region.

## 2. Create a service account
Firebase Console → Project settings → Service accounts → Generate new private key.

Do not commit the downloaded JSON file to GitHub.

For local development you can either:
- save it as `firebase-service-account.json` and set `FIREBASE_SERVICE_ACCOUNT_FILE` to its path, or
- put the entire JSON into `FIREBASE_SERVICE_ACCOUNT_JSON`, or
- base64 encode it and use `FIREBASE_SERVICE_ACCOUNT_JSON_BASE64`.

For Render, `FIREBASE_SERVICE_ACCOUNT_JSON_BASE64` is convenient as an environment variable.

## 3. Storage bucket
Set:
`FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app`
Use the exact bucket name shown in Firebase Storage.

The backend uploads memory attachments to Firebase Storage and stores only metadata/URLs in Firestore.

## 4. Firestore structure
The application creates this structure automatically:

users/{userId}
  email
  first_name
  password
  is_active
  login_welcomed
  created_at

users/{userId}/transactions/{transactionId}
users/{userId}/targets/{YYYY-MM-01}
users/{userId}/activities/{activityId}
users/{userId}/todos/{todoId}
users/{userId}/habits/{habitId}
users/{userId}/habit_logs/{habitId_date_slot}
users/{userId}/memories/{memoryId}
users/{userId}/memories/{memoryId}/attachments/{attachmentId}

otps/{otpId}

## 5. Environment variables
Example:

SECRET_KEY=replace-with-a-long-random-secret
DEBUG=1
FRONTEND_URL=http://localhost:5173

FIREBASE_SERVICE_ACCOUNT_FILE=C:\path\to\firebase-service-account.json
FIREBASE_STORAGE_BUCKET=your-project-id.firebasestorage.app

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

## 6. Install and run
```bash
pip install -r requirements.txt
python manage.py check
python manage.py runserver
```

No `python manage.py migrate` is required for LifePulse data because Firestore is used instead of Django ORM tables.

## 7. Frontend
Keep your existing API base URL:
`VITE_API=https://YOUR-BACKEND/api`

The React API contract remains `/api/auth/...`, `/api/finance/...`, `/api/memories/...`, etc.
