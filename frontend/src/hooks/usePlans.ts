import { useEffect } from "react";
import { usePlansStore } from "../store/plansStore";

export function usePlans() {
  const { plans, fetchPlans, approvePlan, rejectPlan } = usePlansStore();

  useEffect(() => {
    fetchPlans();
  }, []);

  return { plans, approvePlan, rejectPlan };
}
