# Payoneer Integration - Environment Variables Guide

## Backend Environment Variables

Add these to your `.env` file in the `sabi-backend` directory:

```bash
# Payoneer API Configuration
PAYONEER_API_URL=https://api.payoneer.com/v2
PAYONEER_CLIENT_ID=your_client_id_here
PAYONEER_CLIENT_SECRET=your_client_secret_here
PAYONEER_WEBHOOK_SECRET=your_webhook_secret_here
PAYONEER_PARTNER_ID=your_partner_id_here

# Frontend URLs
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

## Frontend Environment Variables

Add these to your `.env.local` file in the `sabi-frontend/frontend` directory:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Getting Payoneer Credentials

1. **Sign up for Payoneer Business Account**:
   - Go to https://www.payoneer.com/business/
   - Create a business account
   - Verify your account and business information

2. **Get API Credentials**:
   - Navigate to your Payoneer Dashboard
   - Go to Settings → API Credentials
   - Create a new API app
   - Copy the `Client ID` and `Client Secret`

3. **Set up Webhooks**:
   - In Payoneer Settings → Webhooks
   - Add webhook URL: `https://yourbackend.com/api/payments/webhook`
   - Copy the webhook secret

4. **Configure Integration**:
   - Add the credentials to your backend `.env`
   - Ensure your backend is accessible from Payoneer's servers
   - Test with sandbox credentials first

## Payment Flow

### Creating a Payment (Frontend)

1. User selects course/program/diploma to purchase
2. Frontend calls `POST /api/payments/checkout` with:
   - `item_type`: 'course' | 'program' | 'diploma'
   - `item_id`: numeric ID
   - `currency`: currency code (gbp, usd, eur, etc)

3. Backend creates payment record and Payoneer checkout session
4. Frontend redirects user to Payoneer checkout URL
5. User completes payment on Payoneer

### Handling Payment Confirmation (Backend)

1. Payoneer sends webhook to `/api/payments/webhook`
2. Backend verifies webhook signature
3. Backend updates payment status
4. On completion, automatic enrollment is created
5. User gains access to purchased content

### After Payment

- Success: User is redirected to `/payment/success`
- Failure/Cancel: User is redirected to `/payment/cancel`
- Email confirmation sent to user

## Testing

### Local Development

Use Payoneer's sandbox environment:

```bash
PAYONEER_API_URL=https://api.sandbox.payoneer.com/v2
PAYONEER_CLIENT_ID=your_sandbox_client_id
PAYONEER_CLIENT_SECRET=your_sandbox_client_secret
```

### Test Payment Methods

Payoneer provides test cards for sandbox:
- Test Card: 4111 1111 1111 1111
- Expiry: Any future date
- CVV: Any 3 digits

## Troubleshooting

### "Failed to authenticate with Payoneer"
- Check PAYONEER_CLIENT_ID and PAYONEER_CLIENT_SECRET are correct
- Ensure API URL is correct for your environment (sandbox vs production)

### "Webhook signature invalid"
- Verify PAYONEER_WEBHOOK_SECRET matches Payoneer settings
- Ensure webhook endpoint is publicly accessible

### "Payment status not updating"
- Check backend logs for webhook processing errors
- Verify database connection and models are correct
- Ensure payment record exists before webhook is received

## API Endpoints

### Public Endpoints

- `POST /api/payments/checkout` - Initiate checkout
- `GET /api/payments/status/{payment_id}` - Get payment status
- `POST /api/payments/webhook` - Payoneer webhook handler

### Additional Features (Future)

- Admin payment management dashboard
- Payment analytics and reporting
- Refund processing
- Subscription billing
- Multi-currency support
- Payment method options

## Support

For Payoneer API support: https://developer.payoneer.com/docs/
For integration issues: Check backend logs and webhook events in Payoneer dashboard
