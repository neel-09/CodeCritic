from typing_extensions import TypedDict

class State(TypedDict):

    user_prompt : str
    target_board : str
    target_fqbn : str
    sketch_ino : str
    diag_json : str
    lib_txt : str
    compile_error : list[str]
    retry_count : int
    complexity_score : int
    session_id : str
    pass_score : float
    assertion_diff : dict
    clarification_needed : bool
    clarification_question : str
    code_spec : dict
    circuit_spec : dict
    error_log : dict
    hex_path : str
    simulation_feedback : str
    serial_output : str
    vcd_data : str
    exit_code : int
    dsl_assertions: list
    spec_hash: str
    cache_hit: bool = False
    prompt_hash: str = ""