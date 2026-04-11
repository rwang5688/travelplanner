permit (
  principal,
  action == AgentCore::Action::"flights___search_flights_by_budget",
  resource == AgentCore::Gateway::"arn:aws:bedrock-agentcore:us-east-1:539307129890:gateway/travelplanner-travel-planner-gateway-me5u5t9ltj"
) when {
  context.input has max_price && context.input.max_price <= 1000
};
