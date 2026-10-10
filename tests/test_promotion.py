import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from src import figures
from tests import test_pipeline as pipeline
import importlib.util
import os

class PromotionChecks(unittest.TestCase):
    setUp = pipeline.PipelineTest.setUp
    write_raw = pipeline.PipelineTest.write_raw
    run_cli = pipeline.PipelineTest.run_cli
    assert_success = pipeline.PipelineTest.assert_success
    seed_outputs = pipeline.PipelineTest.seed_outputs
    def test_late_figure_promotion_preserves_complete_generation(self):
        self.write_raw(pipeline.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        names = [name + suffix + '.png' for name in ('f1_town_dumbbell','f2_rolling_median','f3_mix_drift','f4_waterfall') for suffix in ('','-dark')]
        destinations = [self.root / folder / name for folder in ('reports/figures','docs/img') for name in names]
        for path in destinations:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'prior-' + path.name.encode())
        spec = importlib.util.spec_from_file_location('isolated_figures', self.root / 'src/figures.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = os.replace
        failed = False
        def fail_late(source, target):
            nonlocal failed
            if not failed and Path(target) == destinations[-1]:
                failed = True
                raise OSError('injected late promotion')
            return original(source, target)
        cwd = Path.cwd()
        try:
            with patch('os.replace', fail_late):
                with self.assertRaises(OSError):
                    module.main()
        finally:
            os.chdir(cwd)
        for path in destinations:
            self.assertEqual(path.read_bytes(), b'prior-' + path.name.encode())

    def test_late_analysis_promotion_preserves_csv_pair(self):
        from src import analysis
        self.write_raw(pipeline.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        self.seed_outputs()
        original = os.replace
        failed = False
        def fail_second(source, target):
            nonlocal failed
            if not failed and Path(target).name == 'sensitivity.csv':
                failed = True
                raise OSError('injected second CSV promotion')
            return original(source, target)
        cwd = Path.cwd()
        try:
            with patch.object(analysis, 'ROOT', self.root), patch.object(analysis, 'PARQUET', str(self.parquet)), patch.object(analysis, 'OUT', self.root / 'outputs'), patch('os.replace', fail_second):
                with self.assertRaises(OSError):
                    analysis.main()
        finally:
            os.chdir(cwd)
        for name in ('town_4room_yoy.csv', 'sensitivity.csv'):
            self.assertEqual((self.root / 'outputs' / name).read_bytes(), b'old CSV sentinel\n')

    def test_late_figure_save_preserves_complete_generation(self):
        self.write_raw(pipeline.fixture_rows())
        self.assert_success(self.run_cli('build_dataset.py'))
        names = [name + suffix + '.png' for name in ('f1_town_dumbbell','f2_rolling_median','f3_mix_drift','f4_waterfall') for suffix in ('','-dark')]
        destinations = [self.root / folder / name for folder in ('reports/figures','docs/img') for name in names]
        for path in destinations:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'prior-' + path.name.encode())
        spec = importlib.util.spec_from_file_location('isolated_figures', self.root / 'src/figures.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.plt.Figure.savefig
        calls = 0
        def fail_second(fig, *args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected second save')
            return original(fig, *args, **kwargs)
        cwd = Path.cwd()
        try:
            with patch.object(module.plt.Figure, 'savefig', fail_second):
                with self.assertRaises(OSError):
                    module.main()
        finally:
            os.chdir(cwd)
        for path in destinations:
            self.assertEqual(path.read_bytes(), b'prior-' + path.name.encode())
