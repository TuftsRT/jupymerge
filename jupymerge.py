import json
import argparse
from typing import List, Optional, Dict, Any, Union


def find_cell_index(
    cells: List[Dict[str, Any]], cell_id_or_index: Union[str, int]
) -> int:
    if isinstance(cell_id_or_index, int):
        return cell_id_or_index
    return next(
        i for i, cell in enumerate(cells) if cell["metadata"]["id"] == cell_id_or_index
    )


def insert_cells(
    dest_cells: List[Dict[str, Any]],
    cells_to_insert: List[Dict[str, Any]],
    place_before_id_or_index: Optional[Union[str, int]] = None,
    place_after_id_or_index: Optional[Union[str, int]] = None,
    place_at_top: bool = False,
    place_at_bottom: bool = False,
) -> List[Dict[str, Any]]:
    if place_at_top:
        return cells_to_insert + dest_cells
    elif place_at_bottom:
        return dest_cells + cells_to_insert
    elif place_before_id_or_index is not None:
        place_before_index = find_cell_index(dest_cells, place_before_id_or_index)
        return (
            dest_cells[:place_before_index]
            + cells_to_insert
            + dest_cells[place_before_index:]
        )
    elif place_after_id_or_index is not None:
        place_after_index = find_cell_index(dest_cells, place_after_id_or_index)
        return (
            dest_cells[: place_after_index + 1]
            + cells_to_insert
            + dest_cells[place_after_index + 1 :]
        )
    else:
        return dest_cells + cells_to_insert


def load_notebook(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_notebook(file_path: str, data: Dict[str, Any]) -> None:
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def extract_cells_from_source(
    source_data: Dict[str, Any],
    cell_ids_or_indexes: Optional[List[Union[str, int]]],
    before_id_or_index: Optional[Union[str, int]],
    after_id_or_index: Optional[Union[str, int]],
    all_cells: bool,
    top_n: Optional[int],
    bottom_n: Optional[int],
) -> List[Dict[str, Any]]:
    if all_cells:
        return source_data["cells"]
    elif cell_ids_or_indexes:
        return [
            cell
            for i, cell in enumerate(source_data["cells"])
            if i in cell_ids_or_indexes or cell["metadata"]["id"] in cell_ids_or_indexes
        ]
    elif before_id_or_index is not None:
        before_index = find_cell_index(source_data["cells"], before_id_or_index)
        return source_data["cells"][:before_index]
    elif after_id_or_index is not None:
        after_index = find_cell_index(source_data["cells"], after_id_or_index)
        return source_data["cells"][after_index + 1 :]
    elif top_n is not None:
        if top_n < 0:
            return source_data["cells"][:top_n]
        return source_data["cells"][:top_n]
    elif bottom_n is not None:
        if bottom_n < 0:
            return source_data["cells"][-bottom_n:]
        return source_data["cells"][-bottom_n:]
    else:
        raise ValueError(
            "You must specify either cell_ids_or_indexes, before_id_or_index, after_id_or_index, all_cells, top_n, or bottom_n"
        )


def convert_to_int_if_needed(value: Optional[str]) -> Optional[Union[str, int]]:
    if value is None:
        return None
    return int(value) if value.isdigit() else value


def extract_cells(
    source_nb: str,
    dest_nb: str,
    cell_ids_or_indexes: Optional[List[Union[str, int]]] = None,
    before_id_or_index: Optional[Union[str, int]] = None,
    after_id_or_index: Optional[Union[str, int]] = None,
    all_cells: bool = False,
    place_before_id_or_index: Optional[Union[str, int]] = None,
    place_after_id_or_index: Optional[Union[str, int]] = None,
    place_at_top: bool = False,
    place_at_bottom: bool = False,
    top_n: Optional[int] = None,
    bottom_n: Optional[int] = None,
) -> None:
    source_data = load_notebook(source_nb)
    dest_data = load_notebook(dest_nb)

    cells_to_extract = extract_cells_from_source(
        source_data,
        cell_ids_or_indexes,
        before_id_or_index,
        after_id_or_index,
        all_cells,
        top_n,
        bottom_n,
    )
    dest_data["cells"] = insert_cells(
        dest_data["cells"],
        cells_to_extract,
        place_before_id_or_index,
        place_after_id_or_index,
        place_at_top,
        place_at_bottom,
    )

    save_notebook(dest_nb, dest_data)
    print(f"Extracted cells and added to {dest_nb}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract cells from one Jupyter notebook and place them into another."
    )
    parser.add_argument("source_nb", help="Path to the source Jupyter notebook")
    parser.add_argument("dest_nb", help="Path to the destination Jupyter notebook")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--cell_ids_or_indexes", nargs="+", help="GUIDs or indexes of the cells to extract"
    )
    group.add_argument(
        "--before_id_or_index", help="Extract all cells before this cell ID or index"
    )
    group.add_argument(
        "--after_id_or_index", help="Extract all cells after this cell ID or index"
    )
    group.add_argument(
        "--all_cells", action="store_true", help="Extract all cells from the source notebook"
    )
    group.add_argument(
        "--top_n", type=int, help="Extract the top N cells from the source notebook"
    )
    group.add_argument(
        "--bottom_n", type=int, help="Extract the bottom N cells from the source notebook"
    )
    parser.add_argument(
        "--place_before_id_or_index",
        help="Place extracted cells before this cell ID or index in the destination notebook",
    )
    parser.add_argument(
        "--place_after_id_or_index",
        help="Place extracted cells after this cell ID or index in the destination notebook",
    )
    parser.add_argument(
        "--place_at_top", action="store_true", help="Place extracted cells at the top of the destination notebook"
    )
    parser.add_argument(
        "--place_at_bottom",
        action="store_true",
        help="Place extracted cells at the bottom of the destination notebook",
    )

    args = parser.parse_args()

    cell_ids_or_indexes = (
        [convert_to_int_if_needed(x) for x in args.cell_ids_or_indexes]
        if args.cell_ids_or_indexes
        else None
    )
    before_id_or_index = convert_to_int_if_needed(args.before_id_or_index)
    after_id_or_index = convert_to_int_if_needed(args.after_id_or_index)
    place_before_id_or_index = convert_to_int_if_needed(args.place_before_id_or_index)
    place_after_id_or_index = convert_to_int_if_needed(args.place_after_id_or_index)

    extract_cells(
        args.source_nb,
        args.dest_nb,
        cell_ids_or_indexes,
        before_id_or_index,
        after_id_or_index,
        args.all_cells,
        place_before_id_or_index,
        place_after_id_or_index,
        args.place_at_top,
        args.place_at_bottom,
        args.top_n,
        args.bottom_n,
    )


if __name__ == "__main__":
    main()
