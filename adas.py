import pandas as pd
import bar_chart_race as bcr
import matplotlib.pyplot as plt

# Патч для совместимости с pandas 2.x (если у тебя новая версия pandas)
_original_fillna = pd.core.generic.NDFrame.fillna

def _fillna_compat(self, *args, **kwargs):
    method = kwargs.get('method') if 'method' in kwargs else (args[0] if len(args) > 0 and isinstance(args[0], str) else None)
    if method == 'ffill':
        return self.ffill()
    if method == 'bfill':
        return self.bfill()
    return _original_fillna(self, *args, **kwargs)

pd.core.generic.NDFrame.fillna = _fillna_compat

# Данные
data = {
    'Year': ['2015-01-01', '2017-01-01', '2019-01-01', '2021-01-01', '2023-01-01', '2025-01-01', '2027-01-01', '2030-01-01'],
    'LUXURY':    [15, 35, 62, 85, 96, 99, 100, 100],
    'MID-RANGE': [2,  8,  22, 45, 72, 88, 95,  98],
    'ECONOMY':   [0,  1,   5, 12, 31, 54, 78,  92]
}

df = pd.DataFrame(data)
df['Year'] = pd.to_datetime(df['Year'])
df = df.set_index('Year')

# Интерполяция для плавной анимации
df_interpolated = df.resample('MS').interpolate(method='pchip').round(1)

# Стили
plt.rcParams.update({
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'text.color': 'black',
    'font.family': 'sans-serif',
})

fig, ax = plt.subplots(figsize=(6, 10), dpi=120)
plt.subplots_adjust(left=0.32, right=0.88, top=0.92, bottom=0.08)  # top увеличен, чтобы заголовок не обрезался

colors = ['#0057FF', '#00B894', '#6C5CE7']

# Плашка "TURNING POINT"
def summary_func(values, ranks):
    current_date = values.name
    
    if current_date >= pd.Timestamp("2020-01-01"):
        text = "TURNING POINT:\nADAS FOR EVERYONE"
        bbox = dict(
            boxstyle="round,pad=0.45",
            fc="#FFD700",
            ec="black",
            lw=1.6,
            alpha=0.95
        )
    else:
        text = ""
        bbox = dict(alpha=0)

    return {
        'x': 0.5,
        'y': 0.22,
        's': text,
        'ha': 'center',
        'va': 'center',
        'size': 11,
        'weight': 'bold',
        'color': 'black',
        'bbox': bbox
    }

print("Рендерим анимацию...")

bcr.bar_chart_race(
    df=df_interpolated,
    filename='adas_share_by_segment.mp4',
    orientation='h',
    sort='desc',
    n_bars=3,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=5,
    period_length=300,
    dpi=100,
    cmap=colors,

    # Заголовок
    title={
        'label': 'Share of Models with ADAS L2+ by Segment',
        'size': 18,
        'weight': 'bold',
        'color': '#000000',
        'loc': 'center',
        'pad': 20
    },

    period_label={
        'x': 0.95,
        'y': 0.04,
        'ha': 'right',
        'va': 'bottom',
        'size': 24,
        'color': '#202020',
        'weight': 'bold'
    },

    period_summary_func=summary_func,
    fig=fig,
    bar_label_size=12,
    tick_label_size=11,
    shared_fontdict={'weight': 'bold'},
    filter_column_colors=True,
)

print("Готово! Файл сохранён как: adas_share_by_segment.mp4")