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

.PHONY: local-all local-stop

MOCK_MODE ?= true

local-all:
	@echo "Starting all auto-claims services locally (MOCK_MODE=$(MOCK_MODE))..."
	export MOCK_MODE=$(MOCK_MODE) ;\
	$(MAKE) -C assessor-agent local & \
	$(MAKE) -C processor-agent local & \
	$(MAKE) -C repair-shop-agent local & \
	$(MAKE) -C ai-service local & \
	$(MAKE) -C backend local & \
	$(MAKE) -C frontend local & \
	wait

local-stop:
	@echo "Stopping all local services..."
	-pkill -f "uvicorn app.fast_api_app:app"
	-pkill -f "uv run main.py"
	-pkill -f "python main.py"
	-pkill -f "next-dev"
	-pkill -f "next"

