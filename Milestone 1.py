import random

print("=== Livestock Production Simulation (Milestone 1 - Procedural) ===")

# System state
names = ["Cow A", "Cow B", "Cow C", "Cow D", "Cow E"]
weights = [200, 180, 220, 210, 190]
milk = [0]*5
feed = [5, 4.5, 6, 5.5, 4.8]

# Simulation
for d in range(1, 31):
    print(f"\nDay {d} Report:")
    
    for i, n in enumerate(names):
        f = feed[i] + d*0.2 + random.uniform(-0.5, 0.5)
        weights[i] += f * 0.25
        milk[i] += weights[i] * 0.015
        
        status = (
            "underweight!" if weights[i] < 150 else
            "overweight!" if weights[i] > 300 else
            "healthy."
        )
        
        print(f"{n} {status} Weight={weights[i]:.1f}kg, Milk={milk[i]:.1f}L")
    
    print(f"Day {d}: Avg Weight={sum(weights)/5:.1f}kg, "
          f"Avg Milk={sum(milk)/5:.1f}L, "
          f"Total Feed={sum(feed)+d*0.2*5:.1f}kg")

# Final summary
print("\n=== Final Summary ===")
for i, n in enumerate(names):
    print(f"{n}: Weight={weights[i]:.1f}kg, Milk={milk[i]:.1f}L")

print(f"\nTotals: Weight={sum(weights):.1f}kg, Milk={sum(milk):.1f}L")