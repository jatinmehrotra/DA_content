// Advanced Policy: Role-based + amount-based access control
// Demonstrates how AgentCore Identity integrates with Cedar Policy.
//
// In production, your gateway uses JWT authorization.
// Cedar policies then evaluate claims from the user's token.

// Tier-1 support: refunds up to $100
permit(
  principal,
  action == AgentCore::Action::"RefundTarget___process_refund",
  resource == AgentCore::Gateway::"<gateway-arn>"
)
when {
  principal has role && principal.role == "support-tier-1" &&
  context.input.amount < 100
};

// Tier-2 support: refunds up to $5000
permit(
  principal,
  action == AgentCore::Action::"RefundTarget___process_refund",
  resource == AgentCore::Gateway::"<gateway-arn>"
)
when {
  principal has role && principal.role == "support-tier-2" &&
  context.input.amount < 5000
};

// Finance team: unlimited refunds
permit(
  principal,
  action == AgentCore::Action::"RefundTarget___process_refund",
  resource == AgentCore::Gateway::"<gateway-arn>"
)
when {
  principal has department && principal.department == "finance"
};
