# { "Depends": "py-genlayer:test" }

import json
from genlayer import *


class InsurancePlatform(gl.Contract):

    owner: Address
    policy_counter: u256
    total_policies: u256
    total_claims: u256
    total_approved_claims: u256
    policy_data: DynArray[str]

    def __init__(self, owner_address: str):
        self.owner = Address(owner_address)
        self.policy_counter = u256(0)
        self.total_policies = u256(0)
        self.total_claims = u256(0)
        self.total_approved_claims = u256(0)

    @gl.public.view
    def get_policy(self, policy_id: str) -> str:
        holder = self._get(policy_id, "holder")
        if not holder:
            return "Policy not found"
        return (
            f"ID: {policy_id} | "
            f"Holder: {holder} | "
            f"Type: {self._get(policy_id, 'policy_type')} | "
            f"Coverage: {self._get(policy_id, 'coverage')} | "
            f"Status: {self._get(policy_id, 'status')} | "
            f"Claim Status: {self._get(policy_id, 'claim_status')} | "
            f"Claim Decision: {self._get(policy_id, 'claim_decision')} | "
            f"Reasoning: {self._get(policy_id, 'claim_reasoning')}"
        )

    @gl.public.view
    def get_policy_count(self) -> u256:
        return self.policy_counter

    @gl.public.view
    def get_platform_summary(self) -> str:
        return (
            f"GenLayer Decentralized Insurance Platform\n"
            f"Total Policies: {int(self.total_policies)}\n"
            f"Total Claims: {int(self.total_claims)}\n"
            f"Approved Claims: {int(self.total_approved_claims)}"
        )

    @gl.public.write
    def register_policy(
        self,
        policy_type: str,
        coverage_description: str,
        conditions: str,
        coverage_amount: str,
    ) -> str:
        caller = str(gl.message.sender_address)
        policy_id = str(int(self.policy_counter))

        assert policy_type in ("travel", "health", "property", "crypto"), \
            "Policy type must be travel, health, property, or crypto"
        assert len(coverage_description) >= 20, "Coverage description too short"
        assert len(conditions) >= 20, "Conditions too short"

        self._set(policy_id, "holder", caller)
        self._set(policy_id, "policy_type", policy_type)
        self._set(policy_id, "coverage", coverage_description[:400])
        self._set(policy_id, "conditions", conditions[:400])
        self._set(policy_id, "coverage_amount", coverage_amount)
        self._set(policy_id, "status", "active")
        self._set(policy_id, "claim_status", "none")
        self._set(policy_id, "claim_event", "")
        self._set(policy_id, "claim_evidence_url", "")
        self._set(policy_id, "claim_decision", "")
        self._set(policy_id, "claim_reasoning", "")

        self.policy_counter = u256(int(self.policy_counter) + 1)
        self.total_policies = u256(int(self.total_policies) + 1)

        return (
            f"Policy {policy_id} registered. "
            f"Type: {policy_type}. "
            f"Coverage: {coverage_amount}."
        )

    @gl.public.write
    def file_claim(
        self,
        policy_id: str,
        event_description: str,
        evidence_url: str,
    ) -> str:
        assert self._get(policy_id, "status") == "active", "Policy is not active"
        assert self._get(policy_id, "claim_status") == "none", "Claim already filed"
        assert len(event_description) >= 20, "Event description too short"
        assert len(evidence_url) >= 10, "Evidence URL too short"

        self._set(policy_id, "claim_event", event_description[:400])
        self._set(policy_id, "claim_evidence_url", evidence_url)
        self._set(policy_id, "claim_status", "under_review")

        self.total_claims = u256(int(self.total_claims) + 1)

        return (
            f"Claim filed for policy {policy_id}. "
            f"Under review. Call process_claim to trigger AI verification."
        )

    @gl.public.write
    def process_claim(self, policy_id: str) -> str:
        assert self._get(policy_id, "claim_status") == "under_review", \
            "No claim under review for this policy"

        policy_type = self._get(policy_id, "policy_type")
        coverage = self._get(policy_id, "coverage")
        conditions = self._get(policy_id, "conditions")
        coverage_amount = self._get(policy_id, "coverage_amount")
        claim_event = self._get(policy_id, "claim_event")
        evidence_url = self._get(policy_id, "claim_evidence_url")

        def leader_fn():
            web_data = ""
            try:
                response = gl.nondet.web.get(evidence_url)
                raw = response.body.decode("utf-8")
                web_data = raw[:3000]
            except Exception:
                web_data = "Could not fetch evidence content."

            prompt = f"""You are an AI insurance claims adjuster for a decentralized insurance platform.
Evaluate whether this insurance claim should be approved or denied.

Policy Type: {policy_type}
Coverage Description: {coverage}
Policy Conditions: {conditions}
Coverage Amount: {coverage_amount}

Claimed Event:
{claim_event}

Evidence fetched from {evidence_url}:
{web_data}

Evaluate the claim based on these criteria:
1. Does the claimed event match the policy coverage?
2. Does the evidence support that the event actually occurred?
3. Are the policy conditions met?

Respond ONLY with this JSON:
{{"decision": "APPROVED", "confidence": 80, "reasoning": "two sentences explaining the claim decision"}}

decision must be exactly APPROVED or DENIED, confidence is 0 to 100,
reasoning explains whether the event matches the coverage and if evidence supports it.
No extra text."""

            result = gl.nondet.exec_prompt(prompt)
            clean = result.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

            decision = data.get("decision", "DENIED")
            confidence = int(data.get("confidence", 50))
            reasoning = data.get("reasoning", "")

            if decision not in ("APPROVED", "DENIED"):
                decision = "DENIED"
            confidence = max(0, min(100, confidence))

            return json.dumps({
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning
            }, sort_keys=True)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                validator_raw = leader_fn()
                leader_data = json.loads(leader_result.calldata)
                validator_data = json.loads(validator_raw)
                if leader_data["decision"] != validator_data["decision"]:
                    return False
                return abs(leader_data["confidence"] - validator_data["confidence"]) <= 15
            except Exception:
                return False

        raw = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        data = json.loads(raw)

        decision = data["decision"]
        confidence = data["confidence"]
        reasoning = data["reasoning"]

        self._set(policy_id, "claim_decision", decision)
        self._set(policy_id, "claim_reasoning", reasoning)

        if decision == "APPROVED":
            self._set(policy_id, "claim_status", "approved")
            self._set(policy_id, "status", "claimed")
            self.total_approved_claims = u256(int(self.total_approved_claims) + 1)
        else:
            self._set(policy_id, "claim_status", "denied")

        return (
            f"Claim processed for policy {policy_id}. "
            f"Decision: {decision} ({confidence}% confidence). "
            f"{reasoning}"
        )

    @gl.public.write
    def cancel_policy(self, policy_id: str) -> str:
        caller = str(gl.message.sender_address)
        holder = self._get(policy_id, "holder")
        assert holder, "Policy not found"
        assert caller == holder or caller == str(self.owner), \
            "Only the holder or owner can cancel"
        assert self._get(policy_id, "status") == "active", "Policy is not active"

        self._set(policy_id, "status", "cancelled")
        return f"Policy {policy_id} cancelled."

    def _get(self, policy_id: str, field: str) -> str:
        key = f"{policy_id}_{field}:"
        for i in range(len(self.policy_data)):
            if self.policy_data[i].startswith(key):
                return self.policy_data[i][len(key):]
        return ""

    def _set(self, policy_id: str, field: str, value: str) -> None:
        key = f"{policy_id}_{field}:"
        for i in range(len(self.policy_data)):
            if self.policy_data[i].startswith(key):
                self.policy_data[i] = f"{key}{value}"
                return
        self.policy_data.append(f"{key}{value}")
