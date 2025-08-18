/**
 * Environment setup for testing.
 * Sets up environment variables and test configuration.
 */

// Set test environment variables
process.env.NODE_ENV = 'test'
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000/api/v1'
process.env.NEXT_PUBLIC_APP_ENV = 'test'