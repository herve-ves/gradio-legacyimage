import type { FileData } from "@gradio/client";

export function normalise_file(
	file: string | FileData | null,
	root: string,
	root_url: string | null
): FileData | null;

export function normalise_file(
	file: FileData[] | null,
	root: string,
	root_url: string | null
): FileData[] | null;

export function normalise_file(
	file: FileData[] | FileData | null,
	root: string,
	root_url: string | null
): FileData[] | FileData | null;

export function normalise_file(
	file: FileData[] | FileData | string | null,
	root: string,
	root_url: string | null
): FileData[] | FileData | null {
	if (file == null) return null;
	if (typeof file === "string") {
		return {
			name: "file_data",
			data: file
		};
	} else if (Array.isArray(file)) {
		const normalized_file: (FileData | null)[] = [];

		for (const x of file) {
			if (x === null) {
				normalized_file.push(null);
			} else {
				normalized_file.push(normalise_file(x, root, root_url));
			}
		}

		return normalized_file as FileData[];
	} else if (file.is_file) {
		file.data = get_fetchable_url_or_file(file.name, root, root_url);
	} else if (file.is_stream) {
		if (root_url == null) {
			file.data = root + "/stream/" + file.name;
		} else {
			file.data = "/proxy=" + root_url + "stream/" + file.name;
		}
	}
	return file;
}

function is_url(str: string): boolean {
	try {
		const url = new URL(str);
		return url.protocol === "http:" || url.protocol === "https:";
	} catch {
		return false;
	}
}

export function get_fetchable_url_or_file(
	path: string | null,
	root: string,
	root_url: string | null
): string {
	if (path == null) {
		return root_url ? `/proxy=${root_url}file=` : `${root}/file=`;
	}
	if (is_url(path)) {
		return path;
	}
	return root_url ? `/proxy=${root_url}file=${path}` : `${root}/file=${path}`;
}

export const blobToBase64 = (blob: File): Promise<string> => {
	const reader = new FileReader();
	reader.readAsDataURL(blob);
	return new Promise((resolve) => {
		reader.onloadend = (): void => {
			resolve(reader.result as string);
		};
	});
};

export const get_coordinates_of_clicked_image = (
	evt: MouseEvent
): [number, number] | null => {
	let image = evt.currentTarget as HTMLImageElement;

	const imageRect = image.getBoundingClientRect();
	const xScale = image.naturalWidth / imageRect.width;
	const yScale = image.naturalHeight / imageRect.height;
	if (xScale > yScale) {
		const displayed_height = image.naturalHeight / xScale;
		const y_offset = (imageRect.height - displayed_height) / 2;
		var x = Math.round((evt.clientX - imageRect.left) * xScale);
		var y = Math.round((evt.clientY - imageRect.top - y_offset) * xScale);
	} else {
		const displayed_width = image.naturalWidth / yScale;
		const x_offset = (imageRect.width - displayed_width) / 2;
		var x = Math.round((evt.clientX - imageRect.left - x_offset) * yScale);
		var y = Math.round((evt.clientY - imageRect.top) * yScale);
	}
	if (x < 0 || x >= image.naturalWidth || y < 0 || y >= image.naturalHeight) {
		return null;
	}
	return [x, y];
};
