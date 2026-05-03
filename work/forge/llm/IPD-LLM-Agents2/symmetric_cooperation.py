"""
Mean cooperation rate per prompt type over episodes
Two rows, three columns: Moral, Optimistic, Neutral / Scot, Cautious, Self Interested
One mean line per subplot (average of agent 0 and agent 1)
"""

import matplotlib.pyplot as plt
import numpy as np

from functions import (
    load_game_files,
    load_json_file,
    create_output_directory,
    save_figure
)


PROMPT_LAYOUT = [
    ['moral', 'optimistic', 'neutral'],
    ['scot', 'cautious', 'selfinterest']
]

PROMPT_DISPLAY = {
    'moral': 'Moral',
    'optimistic': 'Optimistic',
    'neutral': 'Neutral',
    'scot': 'SCoT',
    'cautious': 'Cautious',
    'selfinterest': 'Self Interest'
}

LINE_COLOR = '#1a5276'


def get_prompt_type(data):
    prompts = data.get('prompts', {})
    if 'prompt_type' in prompts:
        pt = prompts['prompt_type']
        if pt == 'system_prompt':
            return 'neutral'
        if pt.startswith('system_prompt_'):
            return pt.replace('system_prompt_', '')
        return pt
    return None


def collect_data(json_files):
    """Collect mean cooperation data grouped by prompt type."""
    data_by_prompt = {}

    for filepath in json_files:
        data = load_json_file(filepath)
        prompt_type = get_prompt_type(data)

        if prompt_type is None:
            continue

        episodes = data.get('episodes', [])
        if not episodes:
            continue

        ep_nums = [ep['episode'] for ep in episodes]
        mean_coop = [
            (ep['agent_0']['cooperation_rate'] + ep['agent_1']['cooperation_rate']) / 2 * 100
            for ep in episodes
        ]

        if prompt_type not in data_by_prompt:
            data_by_prompt[prompt_type] = {}

        for ep, coop in zip(ep_nums, mean_coop):
            data_by_prompt[prompt_type].setdefault(ep, []).append(coop)

    return data_by_prompt


def plot_mean_cooperation_per_prompt(data_by_prompt, output_path):
    """
    One subplot per prompt type, arranged in 2 rows x 3 cols.
    Each subplot shows mean cooperation rate (avg of agent 0 and agent 1) over episodes.
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 10), squeeze=False)
    fig.patch.set_facecolor('white')

    for row_idx, row in enumerate(PROMPT_LAYOUT):
        for col_idx, prompt_key in enumerate(row):
            ax = axes[row_idx][col_idx]
            ax.set_facecolor('white')

            display_name = PROMPT_DISPLAY.get(prompt_key, prompt_key.title())

            if prompt_key not in data_by_prompt:
                ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                       ha='center', va='center', fontsize=16, color='gray')
                ax.set_title(f'Agents with {display_name} Prompt',
                            fontsize=17, fontweight='bold', pad=10, color='#2c3e50')
                continue

            ep_data = data_by_prompt[prompt_key]
            all_episodes = sorted(ep_data.keys())
            mean_coops = [np.mean(ep_data[ep]) for ep in all_episodes]

            ax.plot(all_episodes, mean_coops,
                   color=LINE_COLOR, linewidth=2.5, zorder=10)

            ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3, linewidth=1.5)
            ax.set_xlabel('Episode', fontsize=15, fontweight='bold', color='#2c3e50')
            ax.set_ylabel('Cooperation Rate (%)', fontsize=15, fontweight='bold', color='#2c3e50')
            ax.set_title(f'Agents with {display_name} Prompt',
                        fontsize=17, fontweight='bold', pad=10, color='#2c3e50')
            ax.set_ylim(0, 105)
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=14)
            ax.grid(True, alpha=0.2, color='gray')
            ax.tick_params(labelsize=14, colors='#2c3e50')

    plt.tight_layout(h_pad=6, w_pad=6)
    save_figure(fig, output_path)
    plt.close()
    print(f"✓ Plot saved to: {output_path}")


def save_statistics(data_by_prompt, output_dir):
    """Save mean cooperation rate per prompt type to a txt file."""
    stats_file = output_dir / 'mean_cooperation_per_prompt_stats.txt'

    with open(stats_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("MEAN COOPERATION RATE PER PROMPT TYPE\n")
        f.write("=" * 80 + "\n\n")

        for row in PROMPT_LAYOUT:
            for prompt_key in row:
                display_name = PROMPT_DISPLAY.get(prompt_key, prompt_key.title())

                if prompt_key not in data_by_prompt:
                    f.write(f"{display_name:<20} No data\n")
                    continue

                all_values = [
                    v for ep_vals in data_by_prompt[prompt_key].values()
                    for v in ep_vals
                ]
                overall_mean = np.mean(all_values)
                f.write(f"{display_name:<20} {overall_mean:.2f}%\n")

        f.write("\n")

    print(f"✓ Statistics saved to: {stats_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot mean cooperation rate per prompt type"
    )
    parser.add_argument('--results-dir', type=str, default='results/symmetric',
                       help='Directory containing JSON result files')
    parser.add_argument('--output-dir', type=str, default='graphs_stats',
                       help='Directory to save output plots')
    parser.add_argument('--output-name', type=str,
                       default='mean_cooperation_per_prompt.png',
                       help='Output filename')

    args = parser.parse_args()

    try:
        print(f"Loading game files from {args.results_dir}...")
        json_files = load_game_files(args.results_dir, recursive=True)
        print(f"Found {len(json_files)} JSON files")

        output_dir = create_output_directory(args.output_dir)
        output_path = output_dir / args.output_name

        print("Collecting data...")
        data_by_prompt = collect_data(json_files)

        print("Creating visualization...")
        plot_mean_cooperation_per_prompt(data_by_prompt, output_path)

        print("Saving statistics...")
        save_statistics(data_by_prompt, output_dir)

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