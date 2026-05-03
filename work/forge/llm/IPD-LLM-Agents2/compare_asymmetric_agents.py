"""
Cooperation rates comparison: symmetric vs asymmetric per prompt type
4 subplots: cautious symmetric, cautious asymmetric, moral symmetric, moral asymmetric
"""

import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path

from functions import (
    load_game_files,
    create_output_directory,
    save_figure,
    load_json_file
)


def get_prompt_type(data):
    prompts = data.get('prompts', {})

    def format_pt(pt):
        if pt == 'system_prompt':
            return 'neutral'
        if pt.startswith('system_prompt_'):
            return pt.replace('system_prompt_', '')
        return pt

    if 'prompt_type' in prompts:
        pt = format_pt(prompts['prompt_type'])
        return pt, pt, False
    pt0 = format_pt(prompts.get('prompt_type_0', 'unknown'))
    pt1 = format_pt(prompts.get('prompt_type_1', 'unknown'))
    return pt0, pt1, True


def collect_data(json_files):
    sym_data = defaultdict(lambda: defaultdict(list))
    asym_data = defaultdict(lambda: {'agent_0': [], 'agent_1': []})
    asym_pt0 = None
    asym_pt1 = None

    for filepath in json_files:
        data = load_json_file(filepath)
        pt0, pt1, is_asym = get_prompt_type(data)
        episodes = data.get('episodes', [])

        if is_asym:
            asym_pt0 = pt0
            asym_pt1 = pt1
            for ep in episodes:
                ep_num = ep['episode']
                asym_data[ep_num]['agent_0'].append(ep['agent_0']['cooperation_rate'] * 100)
                asym_data[ep_num]['agent_1'].append(ep['agent_1']['cooperation_rate'] * 100)
        else:
            for ep in episodes:
                ep_num = ep['episode']
                mean_coop = (ep['agent_0']['cooperation_rate'] + ep['agent_1']['cooperation_rate']) / 2 * 100
                sym_data[pt0][ep_num].append(mean_coop)

    return sym_data, asym_data, asym_pt0, asym_pt1


def _plot_single(ax, episodes, values, color, title):
    ax.set_facecolor('white')
    ax.plot(episodes, values, color=color, linewidth=2.5, zorder=10)
    ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3, linewidth=1.5)
    ax.set_xlabel('Episode', fontsize=15, fontweight='bold', color='#2c3e50')
    ax.set_ylabel('Cooperation Rate (%)', fontsize=15, fontweight='bold', color='#2c3e50')
    ax.set_title(title, fontsize=17, fontweight='bold', pad=15, color='#2c3e50')
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=14)
    ax.grid(True, alpha=0.2, color='gray')
    ax.tick_params(labelsize=14, colors='#2c3e50')


def plot_comparison(json_files, output_path):
    sym_data, asym_data, asym_pt0, asym_pt1 = collect_data(json_files)

    # pt0 = moral (agent 0 in asymmetric), pt1 = cautious (agent 1 in asymmetric)
    pt0 = asym_pt0  # moral
    pt1 = asym_pt1  # cautious

    ep_nums_asym = sorted(asym_data.keys()) if asym_data else []

    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.patch.set_facecolor('white')

    # Top left: pt0 agent (moral) — symmetric
    if pt0 in sym_data:
        ep_nums = sorted(sym_data[pt0].keys())
        means = [np.mean(sym_data[pt0][ep]) for ep in ep_nums]
        _plot_single(axes[0][0], ep_nums, means, '#1a66cc',
                    f'{pt0.title()} agent — symmetric')
    else:
        axes[0][0].text(0.5, 0.5, 'No data', transform=axes[0][0].transAxes,
                       ha='center', va='center', fontsize=16, color='gray')
        axes[0][0].set_title(f'{pt0.title()} agent — symmetric',
                            fontsize=17, fontweight='bold', pad=15, color='#2c3e50')

    # Top right: pt0 agent (moral) — asymmetric (agent 0)
    if ep_nums_asym:
        means_asym_0 = [np.mean(asym_data[ep]['agent_0']) for ep in ep_nums_asym]
        _plot_single(axes[0][1], ep_nums_asym, means_asym_0, '#1a66cc',
                    f'{pt0.title()} agent — asymmetric')
    else:
        axes[0][1].text(0.5, 0.5, 'No data', transform=axes[0][1].transAxes,
                       ha='center', va='center', fontsize=16, color='gray')
        axes[0][1].set_title(f'{pt0.title()} agent — asymmetric',
                            fontsize=17, fontweight='bold', pad=15, color='#2c3e50')

    # Bottom left: pt1 agent (cautious) — symmetric
    if pt1 in sym_data:
        ep_nums = sorted(sym_data[pt1].keys())
        means = [np.mean(sym_data[pt1][ep]) for ep in ep_nums]
        _plot_single(axes[1][0], ep_nums, means, '#cc3344',
                    f'{pt1.title()} agent — symmetric')
    else:
        axes[1][0].text(0.5, 0.5, 'No data', transform=axes[1][0].transAxes,
                       ha='center', va='center', fontsize=16, color='gray')
        axes[1][0].set_title(f'{pt1.title()} agent — symmetric',
                            fontsize=17, fontweight='bold', pad=15, color='#2c3e50')

    # Bottom right: pt1 agent (cautious) — asymmetric (agent 1)
    if ep_nums_asym:
        means_asym_1 = [np.mean(asym_data[ep]['agent_1']) for ep in ep_nums_asym]
        _plot_single(axes[1][1], ep_nums_asym, means_asym_1, '#1a66cc',
                    f'{pt1.title()} agent — asymmetric')
    else:
        axes[1][1].text(0.5, 0.5, 'No data', transform=axes[1][1].transAxes,
                       ha='center', va='center', fontsize=16, color='gray')
        axes[1][1].set_title(f'{pt1.title()} agent — asymmetric',
                            fontsize=17, fontweight='bold', pad=15, color='#2c3e50')

    fig.suptitle('Cooperation Rate — Symmetric vs Asymmetric',
                fontsize=22, fontweight='bold', color='#2c3e50')

    plt.tight_layout()
    save_figure(fig, output_path)
    plt.close()
    print(f"✓ Plot saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot cooperation rate comparison: symmetric vs asymmetric"
    )
    parser.add_argument('--results-dir', type=str, default='results',
                       help='Directory containing JSON result files')
    parser.add_argument('--output-dir', type=str, default='graphs_stats',
                       help='Directory to save output plots')
    parser.add_argument('--output-name', type=str,
                       default='cooperation_comparison.png',
                       help='Output filename')

    args = parser.parse_args()

    try:
        print(f"Loading game files from {args.results_dir}...")
        json_files = load_game_files(args.results_dir, recursive=False)
        print(f"Found {len(json_files)} JSON files")

        output_dir = create_output_directory(args.output_dir)
        output_path = output_dir / args.output_name

        print("Creating visualization...")
        plot_comparison(json_files, output_path)

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
    