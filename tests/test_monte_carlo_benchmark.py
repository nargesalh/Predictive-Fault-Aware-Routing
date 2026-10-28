import pytest

from experiments.compare_approximations import run_benchmark


def test_benchmark_includes_monte_carlo_results():
    rows = run_benchmark(
        q_values=[0.1],
        repeats=1,
        mc_trials=50,
        mc_seed=7,
    )

    assert len(rows) == 5

    for row in rows:
        assert 0.0 <= row["mc_estimate"] <= 1.0
        assert row["mc_trials"] == 50
        assert row["mc_seed"] == 7
        assert row["mc_absolute_error"] == pytest.approx(
            abs(row["mc_estimate"] - row["exact_reliability"])
        )


def test_benchmark_rejects_invalid_mc_trials():
    with pytest.raises(ValueError, match="mc_trials"):
        run_benchmark(
            q_values=[0.1],
            repeats=1,
            mc_trials=0,
        )


def test_benchmark_rejects_non_integer_mc_trials():
    with pytest.raises(ValueError, match="mc_trials"):
        run_benchmark(
            q_values=[0.1],
            repeats=1,
            mc_trials=1.5,
        )


def test_benchmark_rejects_invalid_mc_seed():
    with pytest.raises(ValueError, match="mc_seed"):
        run_benchmark(
            q_values=[0.1],
            repeats=1,
            mc_trials=20,
            mc_seed=True,
        )
