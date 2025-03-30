import streamlit as st
import datetime
import itertools
import sys
import os
import re
from collections import OrderedDict
import random
import time # For simulating progress if needed, and for unique keys

# --- Configuration (Copied and adapted from CLI) ---
DEFAULT_OUTPUT_FILENAME_BASE = "wordlist"
MIN_YEAR = 1900
MAX_YEAR = datetime.datetime.now().year + 1
NUMBERS_TO_APPEND_RANGE = (0, 99)
COMMON_NUMBER_SEQUENCES = ["1", "12", "123", "1234", "12345", "7", "007"]
LEET_TARGET_CHARS = 'aeiostlz'

# --- Helper Functions (Copied/adapted from CLI, removed CLI-specific print/input) ---

def validate_date_str(date_str):
    """Validates YYYY-MM-DD format string."""
    if not date_str: return True # Allow empty
    try:
        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
        year = date_obj.year
        if not MIN_YEAR <= year <= MAX_YEAR:
             return False
        return True
    except (ValueError, IndexError):
        return False

def validate_year_str(year_str):
    """Validates a 4-digit year string."""
    if not year_str: return True # Allow empty
    if not year_str.isdigit() or len(year_str) != 4:
        return False
    year = int(year_str)
    if not MIN_YEAR <= year <= MAX_YEAR:
        return False
    return True

def parse_list_input(text_area_content):
    """Parses comma or newline separated input from text_area."""
    if not text_area_content:
        return []
    # Split by comma or newline, strip whitespace, filter empty strings
    items = re.split(r'[,\n]', text_area_content)
    return [item.strip() for item in items if item.strip()]

def generate_date_variations(date_obj):
    """Generates various formats from a datetime object."""
    if not date_obj: return []
    # Ensure it's a datetime object for strftime, date object is fine for day/month/year
    if isinstance(date_obj, datetime.date) and not isinstance(date_obj, datetime.datetime):
        date_obj = datetime.datetime.combine(date_obj, datetime.datetime.min.time())

    variations = set()
    d = date_obj.day
    m = date_obj.month
    y = date_obj.year
    yy = str(y)[-2:]

    formats = [
        f"{d}{m}{y}", f"{d}{m}{yy}", f"{m}{d}{y}", f"{m}{d}{yy}",
        f"{y}{m}{d}", f"{yy}{m}{d}", f"{d:02d}{m:02d}{y}", f"{d:02d}{m:02d}{yy}",
        f"{m:02d}{d:02d}{y}", f"{m:02d}{d:02d}{yy}", f"{y}{m:02d}{d:02d}", f"{yy}{m:02d}{d:02d}",
        f"{d}{m}", f"{m}{d}", f"{d:02d}{m:02d}", f"{m:02d}{d:02d}",
        f"{m}{y}", f"{m}{yy}", f"{m:02d}{y}", f"{m:02d}{yy}",
        f"{d}{y}", f"{d}{yy}", f"{d:02d}{y}", f"{d:02d}{yy}",
        f"{y}", f"{yy}", f"{d}", f"{m}", f"{d:02d}", f"{m:02d}"
    ]
    variations.update(formats)
    try:
        month_full = date_obj.strftime("%B").lower()
        month_abbr = date_obj.strftime("%b").lower()
        variations.add(f"{d}{month_full}")
        variations.add(f"{d:02d}{month_full}")
        variations.add(f"{month_full}{d}")
        # ... (add all other month name variations from CLI version) ...
        variations.add(f"{month_full}{d:02d}")
        variations.add(f"{d}{month_abbr}")
        variations.add(f"{d:02d}{month_abbr}")
        variations.add(f"{month_abbr}{d}")
        variations.add(f"{month_abbr}{d:02d}")
        variations.add(f"{month_full}{y}")
        variations.add(f"{month_full}{yy}")
        variations.add(f"{month_abbr}{y}")
        variations.add(f"{month_abbr}{yy}")
        variations.add(f"{y}{month_full}")
        variations.add(f"{yy}{month_full}")
        variations.add(f"{y}{month_abbr}")
        variations.add(f"{yy}{month_abbr}")
    except ValueError: pass
    return list(variations)

def generate_case_variations(word):
    if not word: return []
    word_str = str(word)
    return list(set([word_str.lower(), word_str.upper(), word_str.capitalize()]))

def apply_leet_speak(word):
    if not word: return []
    word = str(word)
    if not any(c.lower() in LEET_TARGET_CHARS for c in word): return [word]
    leet_map = {'a': ['4', '@'], 'e': ['3'], 'i': ['1', '!', '|'], 'o': ['0'], 's': ['5', '$'], 't': ['7', '+'], 'l': ['1'], 'z': ['2']}
    variations = {word}
    replaceable_indices = [i for i, char in enumerate(word.lower()) if char in leet_map]
    if not replaceable_indices: return [word]
    max_leet_replacements = 4 # Limit complexity further for web app responsiveness
    num_replacements_to_try = min(len(replaceable_indices), max_leet_replacements)
    for k in range(1, num_replacements_to_try + 1):
        for indices_to_replace in itertools.combinations(replaceable_indices, k):
            current_replacements = [leet_map[word[index].lower()] for index in indices_to_replace]
            for leet_combination in itertools.product(*current_replacements):
                temp_word_list = list(word)
                for i, index in enumerate(indices_to_replace):
                     temp_word_list[index] = leet_combination[i]
                variations.add("".join(temp_word_list))
    return list(variations)

def add_affixes(word, prefixes=None, suffixes=None):
    if not word: return []
    word_str = str(word)
    variations = {word_str}
    if prefixes:
        for prefix in prefixes:
             prefix_str = str(prefix)
             if prefix_str: variations.add(prefix_str + word_str)
    if suffixes:
        for suffix in suffixes:
            suffix_str = str(suffix)
            if suffix_str: variations.add(word_str + suffix_str)
    return list(variations)

def combine_elements(list1, list2, separators=None):
    combinations = set()
    if not list1 or not list2: return []
    separators = list(separators) if separators else [""]
    if not separators: separators = [""]
    for item1 in list1:
        item1_str = str(item1).strip()
        if not item1_str: continue
        for item2 in list2:
            item2_str = str(item2).strip()
            if not item2_str: continue
            if item1_str == item2_str and "" in separators: continue
            for sep in separators:
                sep_str = str(sep)
                combinations.add(item1_str + sep_str + item2_str)
                if item1_str != item2_str or sep_str != "":
                    combinations.add(item2_str + sep_str + item1_str)
    return list(combinations)

# --- Streamlit App ---

st.set_page_config(page_title="Interactive Wordlist Generator", layout="wide")

st.title("🐍 Interactive Wordlist Generator")
st.caption("Inspired by CUPP - Fill in target info to generate potential passwords.")
st.caption("All info must be comma seperated (dog, cat, chicken)")

# --- Initialize Session State ---
if 'wordlist' not in st.session_state:
    st.session_state.wordlist = None
if 'wordlist_count' not in st.session_state:
    st.session_state.wordlist_count = 0
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'output_filename' not in st.session_state:
     st.session_state.output_filename = f"{DEFAULT_OUTPUT_FILENAME_BASE}.txt"

# --- Sidebar for Global Settings ---
with st.sidebar:
    st.header("⚙️ Global Settings")
    min_len = st.number_input("Minimum Word Length", min_value=1, max_value=32, value=6, step=1)
    max_len = st.number_input("Maximum Word Length", min_value=1, max_value=64, value=16, step=1)
    special_chars_input = st.text_input("Special Characters to Use", value="!@#$%^&*?_.-")
    unique_special_chars = sorted(list(set(c for c in special_chars_input if c)))

    st.subheader("Years Range (Optional)")
    years_range_enabled = st.checkbox("Add range of years?", value=False)
    year_start = 1990
    year_end = datetime.datetime.now().year
    if years_range_enabled:
        year_start = st.number_input("Start Year", min_value=MIN_YEAR, max_value=MAX_YEAR, value=2000)
        year_end = st.number_input("End Year", min_value=MIN_YEAR, max_value=MAX_YEAR, value=datetime.datetime.now().year)


# --- Main Input Form ---
with st.form("wordlist_input_form"):
    st.header("🎯 Target Information")
    st.markdown("_(Fill in as much as possible. Leave fields blank if unknown.)_")

    # --- Organize Inputs with Expanders ---
    with st.expander("👤 Personal Info", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("First Name")
            nicknames_str = st.text_area("Nickname(s)", help="Enter one per line or comma-separated")
        with col2:
            last_name = st.text_input("Last Name")
            # Use min_value slightly before MIN_YEAR to allow None default
            birth_date = st.date_input("Birth Date (YYYY-MM-DD)", value=None, min_value=datetime.date(MIN_YEAR-1, 1, 1), max_value=datetime.date(MAX_YEAR, 12, 31))

    with st.expander("❤️ Partner Info"):
        col1, col2 = st.columns(2)
        with col1:
            partner_first_name = st.text_input("Partner's First Name")
            partner_nicknames_str = st.text_area("Partner's Nickname(s)", help="Enter one per line or comma-separated")
        with col2:
            partner_last_name = st.text_input("Partner's Last Name (if different)")
            partner_birth_date = st.date_input("Partner's Birth Date", value=None, min_value=datetime.date(MIN_YEAR-1, 1, 1), max_value=datetime.date(MAX_YEAR, 12, 31))
        anniversary_date = st.date_input("Anniversary Date", value=None, min_value=datetime.date(MIN_YEAR-1, 1, 1), max_value=datetime.date(MAX_YEAR, 12, 31))


    with st.expander("👶 Children Info"):
         children_names_str = st.text_area("Children's Name(s)", help="Enter one per line or comma-separated")
         children_nicknames_str = st.text_area("Children's Nickname(s)", help="Enter one per line or comma-separated")
         children_birth_dates_str = st.text_area("Children's Birth Date(s) (YYYY-MM-DD)", help="Enter one per line or comma-separated")

    with st.expander("🐾 Pets Info"):
         pet_names_str = st.text_area("Pet Name(s)", help="Enter one per line or comma-separated")

    with st.expander("💼 Work/Location Info"):
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Company Name")
            city = st.text_input("City Name")
            street_name = st.text_input("Street Name")
        with col2:
            job_title = st.text_input("Job Title")
            country = st.text_input("Country Name")


    with st.expander("💡 Interests & Keywords"):
        interests_str = st.text_area("Hobbies/Interests", help="e.g., football, gaming, music (one per line or comma-separated)")
        keywords_str = st.text_area("Other Keywords", help="e.g., favorite color, car model, team (one per line or comma-separated)")


    with st.expander("🔢 Other Numeric Info"):
        important_years_str = st.text_area("Other Important Year(s) (YYYY)", help="Enter one per line or comma-separated")
        lucky_numbers_str = st.text_area("Lucky/Important Number(s)", help="Enter one per line or comma-separated")

    st.divider()

    # --- Augmentation Options within the form ---
    st.subheader("✨ Augmentation Options")
    col_aug1, col_aug2, col_aug3 = st.columns(3)
    with col_aug1:
        add_common_numbers = st.toggle("Append Common Numbers", value=False, help=f"Appends numbers {NUMBERS_TO_APPEND_RANGE[0]}-{NUMBERS_TO_APPEND_RANGE[1]} and sequences like {COMMON_NUMBER_SEQUENCES}")
    with col_aug2:
        use_special_chars_opt = st.toggle("Use Special Chars", value=False, help=f"Uses '{''.join(unique_special_chars)}' as suffixes, separators, and combinations.")
    with col_aug3:
        enable_leet_opt = st.toggle("Enable Leetspeak", value=False, help="Replaces letters with common symbols (e.g., e->3, s->$).")

    st.divider()

    # --- Form Submission ---
    submitted = st.form_submit_button("🚀 Generate Wordlist")

# --- Generation Logic Execution (Outside the form) ---
if submitted:
    st.session_state.generated = False # Reset generation status
    st.session_state.wordlist = None
    st.session_state.wordlist_count = 0

    # --- Prepare Input Data ---
    info = {
        'first_name': first_name, 'last_name': last_name,
        'nicknames': parse_list_input(nicknames_str),
        'birth_date': birth_date, # Keep as date object
        'partner_first_name': partner_first_name, 'partner_last_name': partner_last_name,
        'partner_nicknames': parse_list_input(partner_nicknames_str),
        'partner_birth_date': partner_birth_date,
        'anniversary_date': anniversary_date,
        'children_names': parse_list_input(children_names_str),
        'children_nicknames': parse_list_input(children_nicknames_str),
        'children_birth_dates_str': parse_list_input(children_birth_dates_str), # Keep as string list for now
        'pet_names': parse_list_input(pet_names_str),
        'company_name': company_name, 'job_title': job_title,
        'city': city, 'country': country, 'street_name': street_name,
        'interests': parse_list_input(interests_str),
        'keywords': parse_list_input(keywords_str),
        'important_years': [y for y in parse_list_input(important_years_str) if validate_year_str(y)],
        'lucky_numbers': parse_list_input(lucky_numbers_str)
    }

    # Determine output filename based on first name
    if first_name:
        sanitized_name = re.sub(r'[\\/*?:"<>| ]', '_', str(first_name).lower().strip())
        if not sanitized_name: sanitized_name = DEFAULT_OUTPUT_FILENAME_BASE
        st.session_state.output_filename = f"{sanitized_name}_wordlist.txt"
    else:
        st.session_state.output_filename = f"{DEFAULT_OUTPUT_FILENAME_BASE}.txt"

    st.info(f"Starting wordlist generation for target '{first_name or 'Unknown'}'...")

    # Placeholders for progress bars
    progress_status = st.empty()
    progress_bar_comb = st.progress(0)
    progress_bar_suffix = st.progress(0)
    progress_bar_leet = st.progress(0)

    try: # Wrap generation in try/except
        # --- Process Collected Data ---
        progress_status.write("Processing base words and dates...")
        base_words = set()
        string_collections = [
            [info.get('first_name')], [info.get('last_name')], info.get('nicknames', []),
            [info.get('partner_first_name')], [info.get('partner_last_name')], info.get('partner_nicknames', []),
            info.get('children_names', []), info.get('children_nicknames', []),
            info.get('pet_names', []), [info.get('company_name')], [info.get('job_title')],
            [info.get('city')], [info.get('country')], [info.get('street_name')],
            info.get('interests', []), info.get('keywords', [])
        ]

        for collection in string_collections:
            if collection:
                for item in collection:
                    if item:
                        item_str = str(item)
                        base_words.update(generate_case_variations(item_str))
                        if len(item_str) > 2:
                            base_words.add(item_str[::-1].lower())
                            base_words.add(item_str[::-1].capitalize())
                        base_words.add(item_str.lower())

        # Process Dates
        date_variations = set()
        all_dates = [info.get('birth_date'), info.get('partner_birth_date'), info.get('anniversary_date')]
        children_dates_objs = []
        for date_str in info.get('children_birth_dates_str', []):
             if validate_date_str(date_str):
                  try: children_dates_objs.append(datetime.datetime.strptime(date_str, '%Y-%m-%d').date())
                  except ValueError: pass
        all_dates.extend(children_dates_objs)

        for date_obj in all_dates:
            if date_obj: date_variations.update(generate_date_variations(date_obj))

        # Process Years
        year_nums = set()
        for date_obj in all_dates:
            if date_obj:
                year_nums.add(str(date_obj.year))
                year_nums.add(str(date_obj.year)[-2:])
        year_nums.update(info.get('important_years', []))
        if years_range_enabled:
            if year_start <= year_end:
                for y in range(year_start, year_end + 1):
                    year_nums.add(str(y))
                    year_nums.add(str(y)[-2:])

        # Combine Numeric Elements
        numeric_elements = list(date_variations) + list(year_nums) + info.get('lucky_numbers', [])
        numeric_elements = {str(n).strip() for n in numeric_elements if n}
        core_strings = list({str(w).lower() for w in base_words if w})
        all_numeric_affixes = list(numeric_elements)

        # --- Generate Wordlist ---
        progress_status.write("Generating combinations...")
        final_wordlist = set()
        final_wordlist.update(base_words)
        final_wordlist.update(all_numeric_affixes)

        # Combine core strings with numeric (simple concat)
        combinations1 = combine_elements(core_strings, all_numeric_affixes, separators=[""])
        final_wordlist.update(combinations1)
        progress_bar_comb.progress(33, text="Combinations: Core + Numeric")

        # Combine core strings with other core strings
        name_parts = []
        if info['first_name']: name_parts.append(str(info['first_name']).lower())
        if info['last_name']: name_parts.append(str(info['last_name']).lower())
        name_parts.extend([str(n).lower() for n in info.get('nicknames', []) if n])
        interest_kws = []
        interest_kws.extend([str(w).lower() for w in info.get('interests', []) if w])
        interest_kws.extend([str(k).lower() for k in info.get('keywords', []) if k])

        word_word_separators = ["", "_", "."]
        if use_special_chars_opt and unique_special_chars:
            word_word_separators.extend(unique_special_chars)

        if name_parts and interest_kws:
            combinations2 = combine_elements(name_parts, interest_kws, separators=word_word_separators)
            final_wordlist.update(combinations2)
        progress_bar_comb.progress(66, text="Combinations: Names + Interests")

        if info['first_name'] and info['last_name']:
             combinations3 = combine_elements([str(info['first_name']).lower()], [str(info['last_name']).lower()], separators=word_word_separators)
             final_wordlist.update(combinations3)
        progress_bar_comb.progress(100, text="Combinations: Complete!")
        time.sleep(0.5) # Pause briefly

        # --- Apply Suffixes ---
        progress_status.write("Applying suffixes...")
        mutated_wordlist = set(final_wordlist)
        suffixes_to_add = set()
        if add_common_numbers:
            start, end = NUMBERS_TO_APPEND_RANGE
            suffixes_to_add.update([str(i) for i in range(start, end + 1)])
            suffixes_to_add.update(COMMON_NUMBER_SEQUENCES)
        if use_special_chars_opt and unique_special_chars:
            suffixes_to_add.update(unique_special_chars)
            if len(unique_special_chars) >= 2:
                max_special_combo_len = 3
                limit = min(max_special_combo_len + 1, len(unique_special_chars) + 1)
                for i in range(2, limit):
                    for combo_tuple in itertools.combinations(unique_special_chars, i):
                        suffixes_to_add.add("".join(combo_tuple))
        suffixes_to_add.update(all_numeric_affixes)
        final_suffixes_list = sorted(list(suffixes_to_add), key=len)

        if final_suffixes_list:
            words_to_mutate_suffix = list(mutated_wordlist)
            total_suffix_words = len(words_to_mutate_suffix)
            newly_suffixed_words = set()
            for i, word in enumerate(words_to_mutate_suffix):
                word_str = str(word)
                if len(word_str) < max_len :
                    relevant_suffixes = [s for s in final_suffixes_list if len(word_str) + len(str(s)) <= max_len]
                    if relevant_suffixes:
                         newly_suffixed_words.update(add_affixes(word_str, suffixes=relevant_suffixes))
                if i % 1000 == 0 or i == total_suffix_words - 1: # Update progress periodically
                    percentage = int(((i + 1) / total_suffix_words) * 100)
                    progress_bar_suffix.progress(percentage, text=f"Suffixes: Processing {i+1}/{total_suffix_words} ({percentage}%)")

            mutated_wordlist.update(newly_suffixed_words)
        progress_bar_suffix.progress(100, text="Suffixes: Complete!")
        time.sleep(0.5)

        # --- Apply Leetspeak ---
        activate_leet = enable_leet_opt # Use the prompt result directly
        if activate_leet:
            progress_status.write("Applying leetspeak...")
            words_to_mutate_leet = list(mutated_wordlist)
            total_leet_words = len(words_to_mutate_leet)
            newly_leeted_words = set()
            for i, word in enumerate(words_to_mutate_leet):
                word_str = str(word)
                leet_variations = apply_leet_speak(word_str) # Internal check for target chars
                newly_leeted_words.update({lw for lw in leet_variations if len(lw) <= max_len})
                if i % 1000 == 0 or i == total_leet_words - 1:
                    percentage = int(((i + 1) / total_leet_words) * 100)
                    progress_bar_leet.progress(percentage, text=f"Leetspeak: Processing {i+1}/{total_leet_words} ({percentage}%)")
            mutated_wordlist.update(newly_leeted_words)
            progress_bar_leet.progress(100, text="Leetspeak: Complete!")
            time.sleep(0.5)
        else:
            progress_bar_leet.progress(100, text="Leetspeak: Skipped")


        # --- Final Filtering ---
        progress_status.write("Applying final length filter...")
        filtered_list = {str(word) for word in mutated_wordlist if min_len <= len(str(word)) <= max_len}

        st.session_state.wordlist = filtered_list
        st.session_state.wordlist_count = len(filtered_list)
        st.session_state.generated = True
        progress_status.empty() # Clear status message
        st.success(f"✅ Wordlist generation complete! Found {st.session_state.wordlist_count} potential passwords.")

    except Exception as e:
         progress_status.empty()
         st.error(f"An error occurred during generation: {e}")
         import traceback
         st.exception(traceback.format_exc()) # Show detailed traceback in app
         st.session_state.generated = False


# --- Display Results and Download Button (Outside the form, appears after generation) ---
if st.session_state.generated and st.session_state.wordlist is not None:
    st.subheader("📊 Results")
    st.write(f"**Total words generated:** {st.session_state.wordlist_count}")

    # Prepare data for download
    if st.session_state.wordlist_count > 0:
        # Sort the set before joining
        sorted_wordlist = sorted(list(st.session_state.wordlist))
        data_to_download = "\n".join(sorted_wordlist) + "\n" # Add trailing newline

        st.download_button(
            label=f"💾 Download {st.session_state.output_filename}",
            data=data_to_download,
            file_name=st.session_state.output_filename,
            mime='text/plain',
            key='download-button' # Add a key
        )
    else:
        st.warning("No words generated matching the criteria.")

elif submitted and not st.session_state.generated:
    # Handle case where generation finished but produced nothing or errored before setting generated=True
     if st.session_state.wordlist_count == 0:
          st.warning("No words generated matching the criteria.")
     # Error message is handled within the try/except block


# --- Footer ---
st.markdown("---")
st.caption("Wordlist Generator based on CUPP principles. Use responsibly and ethically.")
