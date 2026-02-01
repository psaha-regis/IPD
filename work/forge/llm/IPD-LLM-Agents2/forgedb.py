import argparse, json, logging, os, psycopg
from psycopg.rows import dict_row

script_dir = os.path.dirname(os.path.abspath(__file__))

# Set up logging (at top of file, after imports)
logging.basicConfig(
    filename=os.path.join(script_dir, 'forgedb.log'),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class ForgeDB:
    def __init__(self, host='platinum', dbname='forge', user=None):
        """Initialize connection to the forge database."""
        if user is None:
            import getpass
            user = getpass.getuser()
        
        self.conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            row_factory=dict_row
        )
    
    def close(self):
        """Close the database connection."""
        self.conn.close()

    def load_json(self, filepath):
        """
        Import a JSON file into the database.
        
        The INSERT uses parameterized queries where %(name)s placeholders
        are replaced with values from a dictionary. This prevents SQL
        injection and handles type conversion automatically.
        """

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Insert into results table, retrieve serialized results_id from insert
            with self.conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO ipd2.results (
                        timestamp
                        ,hostname
                        ,username
                        ,elapsed_seconds
                        ,cfg_num_episodes
                        ,cfg_round_per_episode
                        ,cfg_total_rounds
                        ,cfg_history_window_size
                        ,cfg_temperature
                        ,cfg_reset_between_episodes
                        ,cfg_reflection_type
                        ,cfg_decision_token_limit
                        ,cfg_reflection_token_limit
                        ,cfg_http_timeout
                        ,cfg_force_decision_retries
                        ,system_prompt
                        ,reflection_template
                        ,raw_json
                    ) VALUES (
                        %(timestamp)s
                        ,%(hostname)s
                        ,%(username)s
                        ,%(elapsed_seconds)s
                        ,%(num_episodes)s
                        ,%(rounds_per_episode)s
                        ,%(total_rounds)s
                        ,%(history_window_size)s
                        ,%(temperature)s
                        ,%(reset_between_episodes)s
                        ,%(reflection_type)s
                        ,%(decision_token_limit)s
                        ,%(reflection_token_limit)s
                        ,%(http_timeout)s
                        ,%(force_decision_retries)s
                        ,%(system_prompt)s
                        ,%(reflection_template)s
                        ,%(raw_json)s
                    ) RETURNING results_id
                    """, 
                    {
                        # Session metadata
                        'timestamp':                data['timestamp'],
                        'hostname':                 data.get('hostname', None),
                        'username':                 data.get('username', None),
                        'elapsed_seconds':          data['elapsed_seconds'],
                        
                        # Config fields
                        'num_episodes':             data['config']['num_episodes'],
                        'rounds_per_episode':       data['config']['rounds_per_episode'],
                        'total_rounds':             data['config']['total_rounds'],
                        'history_window_size':      data['config']['history_window_size'],
                        'temperature':              data['config']['temperature'],
                        'reset_between_episodes':   data['config']['reset_between_episodes'],
                        'reflection_type':          data['config']['reflection_type'],
                        'decision_token_limit':     data['config']['decision_token_limit'],
                        'reflection_token_limit':   data['config']['reflection_token_limit'],
                        'http_timeout':             data['config']['http_timeout'],
                        'force_decision_retries':   data['config']['force_decision_retries'],
                        
                        # Prompts
                        'system_prompt':            data['prompts']['system_prompt'],
                        'reflection_template':      data['prompts']['reflection_template'],
                        
                        # Raw JSON
                        'raw_json':                 json.dumps(data)
                    })
                
                # Retrieve the serialized key generated for the results table
                results_id = cur.fetchone()['results_id']
            
                # Insert into llm_agents table (variable number of agents)
                agent_idx = 0
                while f'agent_{agent_idx}' in data:
                    agent_key = f'agent_{agent_idx}'
                    host_key = f'host_{agent_idx}'
                    model_key = f'model_{agent_idx}'
                    
                    cur.execute("""
                        INSERT INTO ipd2.llm_agents (
                            results_id
                            ,agent_idx
                            ,host
                            ,agent_model
                            ,cfg_model
                            ,total_score
                            ,total_cooperations
                            ,overall_cooperation_rate
                        ) VALUES (
                            %(results_id)s
                            ,%(agent_idx)s
                            ,%(host)s
                            ,%(agent_model)s
                            ,%(cfg_model)s
                            ,%(total_score)s
                            ,%(total_cooperations)s
                            ,%(overall_cooperation_rate)s
                        )
                    """,
                    {
                        'results_id':              results_id,
                        'agent_idx':               agent_idx,
                        'host':                    data.get(host_key, None),
                        'agent_model':             data[agent_key]['model'],
                        'cfg_model':               data['config'][model_key],
                        'total_score':             data[agent_key]['total_score'],
                        'total_cooperations':      data[agent_key]['total_cooperations'],
                        'overall_cooperation_rate': data[agent_key]['overall_cooperation_rate']
                    })
                    
                    agent_idx += 1

                # Insert into episodes table
                for episode_data in data['episodes']:
                    episode_num = episode_data['episode']
                    
                    # Loop through agents for this episode
                    agent_idx = 0
                    while f'agent_{agent_idx}' in episode_data:
                        agent_key = f'agent_{agent_idx}'
                        
                        cur.execute("""
                            INSERT INTO ipd2.episodes (
                                results_id
                                ,agent_idx
                                ,episode
                                ,score
                                ,cooperations
                                ,cooperation_rate
                                ,reflection
                            ) VALUES (
                                %(results_id)s
                                ,%(agent_idx)s
                                ,%(episode)s
                                ,%(score)s
                                ,%(cooperations)s
                                ,%(cooperation_rate)s
                                ,%(reflection)s
                            ) RETURNING episode_id
                        """,
                        {
                            'results_id':       results_id,
                            'agent_idx':        agent_idx,
                            'episode':          episode_num,
                            'score':            episode_data[agent_key]['episode_score'],
                            'cooperations':     episode_data[agent_key]['cooperations'],
                            'cooperation_rate': episode_data[agent_key]['cooperation_rate'],
                            'reflection':       episode_data[agent_key]['reflection']
                        })
                        
                        episode_id = cur.fetchone()['episode_id']
                        
                        # Insert rounds for this episode/agent
                        for round_data in episode_data['rounds']:
                            action_key = f'agent_{agent_idx}_action'
                            reasoning_key = f'agent_{agent_idx}_reasoning'
                            payoff_key = f'agent_{agent_idx}_payoff'
                            ep_score_key = f'agent_{agent_idx}_episode_score'
                            
                            cur.execute("""
                                INSERT INTO ipd2.rounds (
                                    episode_id
                                    ,round
                                    ,action
                                    ,payoff
                                    ,ep_cumulative_score
                                    ,reasoning
                                ) VALUES (
                                    %(episode_id)s
                                    ,%(round)s
                                    ,%(action)s
                                    ,%(payoff)s
                                    ,%(ep_cumulative_score)s
                                    ,%(reasoning)s
                                )
                            """,
                            {
                                'episode_id':          episode_id,
                                'round':               round_data['round'],
                                'action':              round_data[action_key],
                                'payoff':              round_data[payoff_key],
                                'ep_cumulative_score': round_data[ep_score_key],
                                'reasoning':           round_data[reasoning_key]
                            })
                        
                        agent_idx += 1

            self.conn.commit()
            logging.info(
                f"Loaded {filepath} -> results_id={results_id}, user={data['username']}")
            return (results_id, data['username'])
        
        # Prevent duplicate test results from import
        except psycopg.errors.UniqueViolation as e:
            self.conn.rollback()
            logging.warning(f"Duplicate file skipped: {filepath} - {e}")
            return None
        
        # Unexpected exception occurred
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Failed to load {filepath} - {e}")
            raise


    def load_batch(self, dirpath, pattern='*.json'):
        """Load all JSON files from a directory."""
        import glob
        
        filepaths = glob.glob(os.path.join(dirpath, pattern))
        
        if not filepaths:
            logging.warning(f"No files matching {pattern} in {dirpath}")
            return {'loaded': [], 'skipped': [], 'failed': []}
        
        logging.info(f"Found {len(filepaths)} files in {dirpath}")
        
        results = {
            'loaded': [],
            'skipped': [],
            'failed': []
        }
        
        for filepath in sorted(filepaths):
            try:
                result = self.load_json(filepath)
                
                if result is not None:
                    results['loaded'].append((filepath, result[0], result[1]))
                else:
                    results['skipped'].append(filepath)
                    
            except Exception as e:
                results['failed'].append((filepath, str(e)))
        
        logging.info(f"Batch complete: {len(results['loaded'])} loaded, "
                    f"{len(results['skipped'])} skipped, "
                    f"{len(results['failed'])} failed")
        
        return results


if __name__ == '__main__':

    """
    file_path = os.path.join(script_dir, 'results', 'episodic_game_20260126_172659.json')

    print(f"Current directory is {os.getcwd()}")
    print(f"Script Directory is {script_dir}")
    print(f"File to import: {file_path}")

    db = ForgeDB()
    print(f"Connected to: {db.conn.info.dbname}")
    print(f"User: {db.conn.info.user}")
    print(f"Host: {db.conn.info.host}")

    results_id = db.load_json(file_path)
    print(f"Loaded as resutls_id: {results_id}")
    db.close()
    """

    parser = argparse.ArgumentParser(description='Load IPD game data into PostgreSQL')
    parser.add_argument('path', help='File or directory to load')
    parser.add_argument('--pattern', default='*.json', help='File pattern (default: *.json)')
    
    args = parser.parse_args()
    
    db = ForgeDB()
    
    if os.path.isfile(args.path):
        results_id = db.load_json(args.path)
        print(f"Loaded: results_id {results_id}")
    elif os.path.isdir(args.path):
        results = db.load_batch(args.path, args.pattern)
        print(f"Loaded: {len(results['loaded'])}, Skipped: {len(results['skipped'])}, Failed: {len(results['failed'])}")
    else:
        print(f"Path not found: {args.path}")
    
    db.close()


