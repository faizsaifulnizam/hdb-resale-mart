"""Check real rendered objects for both palettes without comparing PNG pixels."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb
from matplotlib.colors import to_rgba

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src import figures as f


class FigureChecks(unittest.TestCase):
    def test_waterfall_signs_and_extents(self):
        # Deliberately reverse the current source signs; hardcoded hues must fail.
        d = dict(rate=90, mix=-200, inter=-30, total=-140, level_t0=7000)
        for palette in (f.LIGHT, f.DARK):
            with self.subTest(palette=palette['suffix']):
                f.use_palette(palette)
                f.use_series_style(dark=palette is f.DARK)
                with patch.object(f, 'save') as save:
                    f.fig4_waterfall(None, d)
                    fig = save.call_args.args[0]
                    ax = fig.axes[0]
                    self.assertEqual(ax.patches[0].get_facecolor(), to_rgba(palette['teal']))
                    self.assertEqual(ax.patches[1].get_facecolor(), to_rgba(palette['burnt']))
                    self.assertEqual(ax.patches[2].get_facecolor(), to_rgba(palette['burnt']))
                    lo, hi = ax.get_ylim()
                    self.assertLess(lo, -140)
                    self.assertGreater(hi, 90)
                    self.assertNotIn('not mix', ax.get_title(loc='left'))
                    f.plt.close(fig)

    def test_display_exclusions_come_from_rows(self):
        con = duckdb.connect()
        con.execute('CREATE TABLE yoy_4room(town VARCHAR,n_t0 INTEGER,n_t1 INTEGER,med_t0 DOUBLE,med_t1 DOUBLE)')
        con.execute("INSERT INTO yoy_4room VALUES ('A',25,25,5000,5100),('B',1,1,6000,5900)")
        with patch.object(f, 'save') as save:
            f.fig1_dumbbell(con)
            fig = save.call_args.args[0]
            self.assertIn('(1 excluded)', fig.texts[0].get_text())
            f.plt.close(fig)
        con.close()


if __name__ == '__main__':
    unittest.main()
