// Blanket permit for all tools on the travel planner gateway
permit (
  principal,
  action,
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:539307129890:gateway/travelplanner-travel-planner-gateway-me5u5t9ltj"
);
