import pandas as pd
import matplotlib.pyplot as plt

data = {
    "mes": ["Ene", "Feb", "Mar"],
    "ventas": [100, 150, 200]
}

df = pd.DataFrame(data)

print(df)

df.plot(x="mes", y="ventas")
plt.show()