# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# Modified from https://gist.github.com/yermulnik/7e0cf991962680d406692e1db1b551e6 for use on MacOS to sort variables

# https://gist.github.com/yermulnik/7e0cf991962680d406692e1db1b551e6
# Tested with GNU Awk 5.1.0, API: 3.0 (GNU MPFR 4.1.0, GNU MP 6.2.1)
# Usage: cat variables.tf | gawk -f <path-to-file>/vars_sort.awk | tee new.tf; mv new.tf variables.tf
# Note: "chmod +x /path/to/tf_vars_sort.awk" before use
# No licensing; yermulnik@gmail.com, 2021-2024
{
	# skip blank lines at the beginning of file
	if (!resource_type && length($0) == 0) next

	# pick only known Terraform resource definition block types of the 1st level
	# https://github.com/hashicorp/terraform/blob/main/internal/configs/parser_config.go#L92-L230
	switch ($0) {
		# ex: block_type {
		case /^[[:space:]]*(import|locals|moved|removed|terraform)[[:space:]]+{/:
			resource_type = $1
			resource_ident = resource_type "|" block_counter++
			break
		# ex: block_type type_label name_label {
		case /^[[:space:]]*(data|resource)[[:space:]]+("?[[:alnum:]_-]+"?[[:space:]]+){2}{/:
			resource_type = $1
			resource_subtype = $2
			resource_name = $3
			resource_ident = resource_type "|" resource_subtype "|" resource_name
			break
		# ex: block_type name_label {
		case /^[[:space:]]*(check|module|output|provider|variable)[[:space:]]+"?[[:alnum:]_-]+"?[[:space:]]+{/:
			resource_type = $1
			resource_name = $2
			resource_ident = resource_type "|" resource_name
			break
	}
	arr[resource_ident] = arr[resource_ident] ? arr[resource_ident] RS $0 : $0
} END {
	# exit if there was solely empty input
	# (input consisting of multiple empty lines only, counts in as empty input too)
	if (length(arr) == 0) exit
	# declare empty array (the one to hold final result)
	split("", res)
	# case-insensitive string operations in this block
	# (primarily for the `asort()` call below)
	IGNORECASE = 1
	# sort by `resource_ident` which is a key in our case
	asort(arr)

	# blank-lines-fix each block
	for (item in arr) {
		split(arr[item],new_arr,RS)

		# remove multiple blank lines at the end of resource definition block
		while (length(new_arr[length(new_arr)]) == 0) delete new_arr[length(new_arr)]

		# add one single blank line at the end of the resource definition block
		# so that blocks are delimited with a blank like to align with TF code style
		new_arr[length(new_arr)+1] = RS

		# fill resulting array with data from each resource definition block
		for (line in new_arr) {
			# trim whitespaces at the end of each line in resource definition block
			gsub(/[[:space:]]+$/, "", new_arr[line])
			res[length(res)+1] = new_arr[line]
		}
	}

	# ensure there are no extra blank lines at the beginning and end of data
	while (length(res[1]) == 0) delete res[1]
	while (length(res[length(res)]) == 0) delete res[length(res)]

	# print resulting data to stdout
	for (line in res) {
		print res[line]
	}
}