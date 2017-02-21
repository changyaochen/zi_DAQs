# This is the code snippet to plot errorbar with Bokeh basic glyphs
xs = fitted_results['vac(V)'].values.tolist()
ys = fitted_results['f0(Hz)'].values.tolist()
yerrs = fitted_results['f0_err(Hz)'].values.tolist()
err_xs, err_ys = [], []
for x, y, yerr in zip(xs, ys, yerrs):
  err_xs.append((x, x))
  err_ys.append((y - yerr, y + yerr))
  
p2.multi_line(err_xs, err_ys, color = 'red', line_width = 1.5)