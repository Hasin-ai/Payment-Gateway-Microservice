#!/usr/bin/env node

/**
 * Quick test script to verify frontend can connect to backend services
 * Run with: node test-connection.js
 */

const API_BASE_URL = "http://localhost:8080";

async function testEndpoint(name, endpoint, method = "GET", body = null) {
  try {
    const options = {
      method,
      headers: {
        "Content-Type": "application/json",
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    const data = await response.json();

    if (response.ok) {
      console.log(`✅ ${name}: SUCCESS`);
      return { success: true, data };
    } else {
      console.log(`❌ ${name}: FAILED - ${response.status}`);
      return { success: false, error: data };
    }
  } catch (error) {
    console.log(`❌ ${name}: ERROR - ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function runTests() {
  console.log("🚀 Testing Backend Connectivity...\n");

  const tests = [
    {
      name: "System Health",
      endpoint: "/health",
    },
    {
      name: "Circuit Breaker Status",
      endpoint: "/circuit-breaker/status",
    },
    {
      name: "Exchange Rate (USD)",
      endpoint: "/api/rates/api/v1/rates/current?currency=USD",
    },
    {
      name: "User Registration (Test)",
      endpoint: "/api/users/register",
      method: "POST",
      body: {
        email: `test-${Date.now()}@example.com`,
        password: "testpassword123",
        first_name: "Test",
        last_name: "User",
        phone: "+1234567890",
      },
    },
  ];

  let successCount = 0;
  const totalTests = tests.length;

  for (const test of tests) {
    const result = await testEndpoint(
      test.name,
      test.endpoint,
      test.method,
      test.body
    );

    if (result.success) {
      successCount++;
    }

    // Small delay between tests
    await new Promise((resolve) => setTimeout(resolve, 100));
  }

  console.log(`\n📊 Results: ${successCount}/${totalTests} tests passed`);

  if (successCount === totalTests) {
    console.log("🎉 All backend services are accessible!");
    console.log("\n✅ You can now:");
    console.log("   1. Visit http://localhost:3000 to access the frontend");
    console.log("   2. Register a new user at http://localhost:3000/register");
    console.log("   3. Test backend connectivity at http://localhost:3000/test-backend");
    console.log("   4. Debug authentication at http://localhost:3000/debug");
  } else {
    console.log("⚠️  Some services are not responding properly.");
    console.log("\n🔧 Troubleshooting:");
    console.log("   1. Make sure backend services are running:");
    console.log("      cd services && docker-compose ps");
    console.log("   2. Restart services if needed:");
    console.log("      cd services && docker-compose down && docker-compose up -d --build");
    console.log("   3. Check service logs:");
    console.log("      cd services && docker-compose logs -f");
  }
}

// Run the tests
runTests().catch(console.error);