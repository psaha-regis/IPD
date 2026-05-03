"""
Plot Positive Moral (Grouped) for Agent 0 and Agent 1 side by side.
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import defaultdict

from functions import (
    load_game_files,
    load_json_file,
    create_output_directory,
    save_figure
)

from bert_analysis import analyze_game_file, POSITIVE_MORAL


def get_prompt_types(data):
    prompts = data.get('prompts', {})

    def format_prompt_type(pt):
        if pt.startswith('system_prompt_'):
            return pt.replace('system_prompt_', '').replace('_', ' ').title() + ' Prompt'
        return pt

    if 'prompt_type' in prompts:
        pt = format_prompt_type(prompts['prompt_type'])
        return pt, pt
    return (
        format_prompt_type(prompts.get('prompt_type_0', 'unknown')),
        format_prompt_type(prompts.get('prompt_type_1', 'unknown')),
    )


def build_index(results):
    """
    Pre-index results by (agent, episode) -> list of records.
    Avoids repeated linear scans in the plotting loop.
    """
    index = defaultdict(list)
    for r in results:
        index[(r['agent'], r['episode'])].append(r)
    return index


def plot_positive_moral_grouped(json_files, output_path, episodes=None):
    """
    Plot Positive Moral (Grouped) for Agent 0 and Agent 1 side by side.
    Mean line only — no per-game faint lines.

    Args:
        json_files: List of JSON file paths
        output_path: Output file path
        episodes: List of episode numbers to include, or None for all
    """
    results_per_game = []
    metrics_per_game = []
    prompt_type_0 = 'unknown'
    prompt_type_1 = 'unknown'
    seen_prompt_types = set()

    for i, filepath in enumerate(json_files, 1):
        print(f"Processing file {i}/{len(json_files)}: {Path(filepath).name}")
        try:
            data = load_json_file(filepath)
            pt0, pt1 = get_prompt_types(data)

            # Warn if prompt types differ across files
            key = (pt0, pt1)
            if seen_prompt_types and key not in seen_prompt_types:
                print(f"  Warning: prompt types differ from previous files: {key}")
            seen_prompt_types.add(key)
            prompt_type_0, prompt_type_1 = pt0, pt1

            file_results, episode_metrics = analyze_game_file(filepath, game_id=i, episodes=episodes)
            if file_results:
                results_per_game.append(file_results)
                metrics_per_game.append(episode_metrics)
        except Exception as e:
            print(f"  Error: {e}")
            continue

    if not results_per_game:
        print("No results to plot.")
        return

    all_episodes = sorted(set(
        r['episode'] for game in results_per_game for r in game
    ))

    fig, axes = plt.subplots(1, 2, figsize=(18, 5), squeeze=False)
    fig.patch.set_facecolor('white')

    agent_configs = [
        ('agent_0', 'Agent 0', prompt_type_0, '#1a66cc', 'cooperation_rate_0'),
        ('agent_1', 'Agent 1', prompt_type_1, '#cc3344', 'cooperation_rate_1'),
    ]

    for agent_idx, (agent_key, agent_label, prompt_type, color, coop_key) in enumerate(agent_configs):
        ax = axes[0][agent_idx]
        ax.set_facecolor('white')
        ax2 = ax.twinx()

        # Build per-game trajectories using pre-indexed lookup
        game_trajectories = []
        for game_results in results_per_game:
            idx = build_index(game_results)
            ep_pcts = []
            for ep in all_episodes:
                ep_results = idx.get((agent_key, ep), [])
                if ep_results:
                    count = sum(1 for r in ep_results if r['moral_category'] in POSITIVE_MORAL)
                    ep_pcts.append((count / len(ep_results)) * 100)
                else:
                    ep_pcts.append(np.nan)
            game_trajectories.append(ep_pcts)

        mean_pcts = np.nanmean(np.array(game_trajectories), axis=0)

        # Cooperation rate
        coop_trajectories = []
        for game_metrics in metrics_per_game:
            ep_coop = {m['episode']: m[coop_key] * 100 for m in game_metrics}
            coop_trajectories.append([ep_coop.get(ep, np.nan) for ep in all_episodes])

        mean_coop = np.nanmean(np.array(coop_trajectories), axis=0)

        ax.plot(all_episodes, mean_pcts,
                color=color, linewidth=2.5, zorder=10,
                label='Positive Moral Rate')
        ax2.plot(all_episodes, mean_coop,
                 color='#16a085', linewidth=2.5, zorder=9,
                 label='Cooperation Rate')

        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.3, linewidth=1.5)
        ax.set_xlabel('Episode', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_ylabel('% Classified as Positive Moral', fontsize=14, fontweight='bold', color='#2c3e50')
        ax2.set_ylabel('Cooperation Rate (%)', fontsize=14, fontweight='bold', color='#2c3e50')
        ax.set_title(f'{agent_label} — {prompt_type} — Positive Moral (Grouped)',
                     fontsize=16, fontweight='bold', pad=10, color='#2c3e50')
        ax.set_ylim(0, 105)
        ax.set_yticks([0, 25, 50, 75, 100])
        ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=13)
        ax2.set_ylim(0, 105)
        ax.grid(True, alpha=0.2, color='gray')
        ax.tick_params(labelsize=13, colors='#2c3e50')
        ax2.tick_params(axis='y', labelcolor='#2c3e50', labelsize=13)

        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, fontsize=14, loc='lower right', framealpha=0.95)

    episode_str = (
        f" (episodes {', '.join(str(e) for e in episodes)})" if episodes else " (all episodes)"
    )
    fig.suptitle(f'Positive Moral (Grouped) per Agent{episode_str}',
                 fontsize=20, fontweight='bold', color='#2c3e50', y=1.02)

    plt.tight_layout(w_pad=4.0)
    save_figure(fig, output_path)
    plt.close()
    print(f"✓ Plot saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Plot Positive Moral (Grouped) for Agent 0 and Agent 1"
    )
    parser.add_argument('--results-dir', type=str, default='results',
                        help='Directory containing JSON result files')
    parser.add_argument('--output-dir', type=str, default='graphs_stats',
                        help='Directory to save output plots')
    parser.add_argument('--output-name', type=str,
                        default='positive_moral_grouped.png',
                        help='Output filename')
    parser.add_argument('--episodes', type=int, nargs='+', default=None,
                        help='Episode numbers to include. If not specified, all episodes are used.')

    args = parser.parse_args()

    try:
        print(f"Loading game files from {args.results_dir}...")
        json_files = load_game_files(args.results_dir, recursive=False)
        print(f"Found {len(json_files)} JSON files")

        output_dir = create_output_directory(args.output_dir)
        output_path = output_dir / args.output_name

        print("Running analysis and plotting...")
        plot_positive_moral_grouped(json_files, output_path, episodes=args.episodes)

        print("\n✓ Complete!")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
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
    