// Policy: Allow refunds under $1000 only
// This Cedar policy is enforced at the AgentCore Gateway boundary,
// OUTSIDE the agent's code - immune to prompt injection.
//
// Replace <gateway-arn> with your actual gateway ARN after first deploy.
// Or use: agentcore add policy --generate "Only allow refunds under 1000 dollars"

permit(
  principal,
  action == AgentCore::Action::"RefundTarget___process_refund",
  resource == AgentCore::Gateway::"<gateway-arn>"
)
when {
  context.input.amount < 1000
};
