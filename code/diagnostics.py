from ga import createInitialPopulation
from weight_function import coverage, averageWalkingDistanceToStop, spacing_penalty, destination_bonus, estimated_travel_time, transfer_bonus, positionAlongRoute
from config import ROUTE_NUMBER

population = createInitialPopulation()
for b in population[:3]:
    positions = sorted(positionAlongRoute(s) for s in b["stops"])
    gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
    print(f"stops={len(b['stops'])}, gaps={[round(g,4) for g in gaps]}")

for name, fn in [
    ("coverage", coverage),
    ("walking_dist", averageWalkingDistanceToStop),
    ("spacing", spacing_penalty),
    ("dest_bonus", destination_bonus),
    ("travel_time", estimated_travel_time),
    ("transfer", transfer_bonus),
]:
    vals = [fn(b["stops"]) for b in population]
    print(f"{name}: min={min(vals):.1f} max={max(vals):.1f} mean={sum(vals)/len(vals):.1f}")