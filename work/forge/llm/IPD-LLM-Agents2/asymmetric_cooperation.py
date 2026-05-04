"""
Mean cooperation rate per prompt pair (asymmetric games) over episodes.
Each subplot = one unique prompt pair combination.
Each subplot shows two lines: agent with prompt_type_0 and agent with prompt_type_1.
Stats saved per agent per combination.
"""

import matplotlib.pyplot as plt
import numpy as np

from functions import (
    load_game_files,
    load_json_file,
    create_output_directory,
    save_figure
)


LINE_COLORS = ['#1a5276', '#c0392b']  # agent_0, agent_1


def get_prompt_types(data):
    """Extract per-agent prompt types from asymmetric game file."""
    prompts = data.get('prompts', {})
    pt0 = prompts.get('prompt_type_0', '')
    pt1 = prompts.get('prompt_type_1', '')

    def normalize(pt):
        pt = pt.replace('system_prompt_', '')
        if pt == 'system_prompt':
            return 'Neutral'
        elif pt == 'scot':
            return 'SCoT'
        elif pt == 'selfinterest':
            return 'Self Interest'
        else:
            return pt.title()

    return normalize(pt0), normalize(pt1)


def collect_data(json_files):
    """
    Collect per-agent cooperation data grouped by prompt pair.
    
    Returns:
        dict: {
            (pt0, pt1): {
                episode_num: {
                    'agent_0': [coop_rate, ...],
                    'agent_1': [coop_rate, ...]
                }
            }
        }
    """
    data_by_pair = {}

    for filepath in json_files:
        data = load_json_file(filepath)
        pt0, pt1 = get_prompt_types(data)

        if pt0 is None or pt1 is None:
            continue

        # Skip symmetric games (handled by the other script)
        if pt0 == pt1:
            continue

        pair = (pt0, pt1)
        episodes = data.get('episodes', [])
        if not episodes:
            continue

        if pair not in data_by_pair:
            data_by_pair[pair] = {}

        for ep in episodes:
            ep_num = ep['episode']
            coop_0 = ep['agent_0']['cooperation_rate'] * 100
            coop_1 = ep['agent_1']['cooperation_rate'] * 100

            if ep_num not in data_by_pair[pair]:
                data_by_pair[pair][ep_num] = {'agent_0': [], 'agent_1': []}

            data_by_pair[pair][ep_num]['agent_0'].append(coop_0)
            data_by_pair[pair][ep_num]['agent_1'].append(coop_1)

    return data_by_pair


def plot_cooperation_per_pair(data_by_pair, output_path):
    """One subplot per prompt pair, two lines per subplot (one per agent)."""
    pairs = sorted(data_by_pair.keys())
    n = len(pairs)

    if n == 0:
        print("No asymmetric pair data found.")
        return

    ncols = 3
    nrows = (n + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 5 * nrows), squeeze=False)
    fig.patch.set_facecolor('white')

    for idx, pair in enumerate(pairs):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        ax.set_facecolor('white')

        pt0, pt1 = pair
        ep_data = data_by_pair[pair]
        all_episodes = sorted(ep_data.keys())

        mean_0 = [np.mean(ep_data[ep]['agent_0']) for ep in all_episodes]
        mean_1 = [np.mean(ep_data[ep]['agent_1']) for ep in all_episodes]

        ax.plot(all_episodes, mean_0, color=LINE_COLORS[0], linewidth=2.5,
                label=f'Agent 0 ({pt0})', zorder=10)
        ax.plot(all_episodes, mean_1, color=LINE_COLORS[1], linewidth=2.5,
                label=f'Agent 1 ({pt1})', zorder=10)

        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3, linewidth=1.5)
        ax.set_xlabel('Episode', fontsize=15, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('Cooperation Rate (%)', fontsize=15, fontweight='bold', color='#2c3e50')
        ax.set_title(f'{pt0} vs {pt1}',
                     fontsize=17, fontweight='bold', pad=10, color='#2c3e50')
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=14)
        ax.grid(True, alpha=0.2, color='gray')
        ax.tick_params(labelsize=14, colors='#2c3e50')
        ax.legend(fontsize=12)

    # Hide unused subplots
    for idx in range(n, nrows * ncols):
        row, col = divmod(idx, ncols)
        axes[row][col].set_visible(False)

    plt.tight_layout(h_pad=6, w_pad=6)
    save_figure(fig, output_path)
    plt.close()
    print(f" Plot saved to: {output_path}")

def save_statistics(data_by_pair, output_dir):
    """Save per-agent mean cooperation rate per prompt pair."""
    stats_file = output_dir / 'mean_cooperation_per_prompt_pair_stats.txt'

    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("MEAN COOPERATION RATE PER PROMPT PAIR (ASYMMETRIC GAMES)\n")
        f.write("=" * 80 + "\n\n")

        for pair in sorted(data_by_pair.keys()):
            pt0, pt1 = pair
            ep_data = data_by_pair[pair]

            all_0 = [v for ep in ep_data.values() for v in ep['agent_0']]
            all_1 = [v for ep in ep_data.values() for v in ep['agent_1']]

            f.write(f"Pair: {pt0.title()} (Agent 0) vs {pt1.title()} (Agent 1)\n")
            f.write(f"  Agent 0 ({pt0:<15}) mean cooperation: {np.mean(all_0):.2f}%\n")
            f.write(f"  Agent 1 ({pt1:<15}) mean cooperation: {np.mean(all_1):.2f}%\n")
            f.write(f"  Number of games: {len(next(iter(ep_data.values()))['agent_0'])}\n")
            f.write("\n")

    print(f" Statistics saved to: {stats_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot mean cooperation rate per asymmetric prompt pair"
    )
    parser.add_argument('--results-dir', type=str, default='results/asymmetric')
    parser.add_argument('--output-dir', type=str, default='graphs_stats')
    parser.add_argument('--output-name', type=str,
                        default='mean_cooperation_per_prompt_pair.pdf')

    args = parser.parse_args()

    try:
        print(f"Loading game files from {args.results_dir}...")
        json_files = load_game_files(args.results_dir, recursive=True)
        print(f"Found {len(json_files)} JSON files")

        output_dir = create_output_directory(args.output_dir)
        output_path = output_dir / args.output_name

        print("Collecting data...")
        data_by_pair = collect_data(json_files)
        print(f"Found {len(data_by_pair)} unique prompt pairs")

        print("Creating visualization...")
        plot_cooperation_per_pair(data_by_pair, output_path)

        print("Saving statistics...")
        save_statistics(data_by_pair, output_dir)

        print("\n✓ Complete!")
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())