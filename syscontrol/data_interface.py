import datetime
import socket

from syscore.dateutils import SECONDS_PER_HOUR
from syscore.genutils import str2Bool
from syscore.objects import arg_not_supplied, missing_data
from sysdata.data_blob import dataBlob
from syscontrol.mongo_process_control import mongoControlProcessData
from sysdata.private_config import get_private_then_default_key_value
from sysproduction.data.strategies import diagStrategiesConfig



class dataControlProcess(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_object(mongoControlProcessData)
        self.data = data

    def get_dict_of_control_processes(self):
        return self.data.db_control_process.get_dict_of_control_processes()


    def check_if_okay_to_start_process(self, process_name):
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        return self.data.db_control_process.check_if_okay_to_start_process(
            process_name)

    def start_process(self, process_name):
        """

        :param process_name: str
        :return:  success, or if not okay: process_no_run, process_stop, process_running
        """
        return self.data.db_control_process.start_process(process_name)

    def finish_process(self, process_name):
        """

        :param process_name: str
        :return: sucess or failure if can't finish process (maybe already running?)
        """

        return self.data.db_control_process.finish_process(process_name)

    def finish_all_processes(self):

        return self.data.db_control_process.finish_all_processes()

    def check_if_process_status_stopped(self, process_name):
        """

        :param process_name: str
        :return: bool
        """
        return self.data.db_control_process.check_if_process_status_stopped(
            process_name
        )

    def change_status_to_stop(self, process_name):
        self.data.db_control_process.change_status_to_stop(process_name)

    def change_status_to_go(self, process_name):
        self.data.db_control_process.change_status_to_go(process_name)

    def change_status_to_no_run(self, process_name):
        self.data.db_control_process.change_status_to_no_run(process_name)

    def has_process_finished_in_last_day(self, process_name):
        result = self.data.db_control_process.has_process_finished_in_last_day(
            process_name
        )
        return result

    def log_run_for_method(self, process_name: str, method_name: str):
       self.data.db_control_process.log_run_for_method(process_name, method_name)

    def when_method_last_run(self, process_name: str, method_name: str) -> datetime.datetime:
        result = self.data.db_control_process.when_method_last_run(process_name, method_name)
        return result

class diagProcessConfig:
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()
        self.data = data

    def get_config_dict(self, process_name):
        previous_process = self.previous_process_name(process_name)
        start_time = self.get_start_time(process_name)
        end_time = self.get_stop_time(process_name)
        machine_name = self.required_machine_name(process_name)
        method_dict = self.get_all_method_dict_for_process_name(process_name)

        result_dict = dict(
            previous_process=previous_process,
            start_time=start_time,
            end_time=end_time,
            machine_name=machine_name,
            method_dict=method_dict,
        )

        return result_dict

    def get_strategy_dict_for_process(self, process_name, strategy_name):
        this_strategy_dict = self.get_strategy_dict_for_strategy(strategy_name)
        this_process_dict = this_strategy_dict[process_name]

        return this_process_dict

    def has_previous_process_finished_in_last_day(self, process_name):
        previous_process = self.previous_process_name(process_name)
        if previous_process is None:
            return True
        control_process = dataControlProcess(self.data)
        result = control_process.has_process_finished_in_last_day(
            previous_process)

        return result

    def is_it_time_to_run(self, process_name):
        start_time = self.get_start_time(process_name)
        stop_time = self.get_stop_time(process_name)
        now_time = datetime.datetime.now().time()

        if now_time >= start_time and now_time < stop_time:
            return True
        else:
            return False

    def is_this_correct_machine(self, process_name):
        required_host = self.required_machine_name(process_name)
        if required_host is None:
            return True

        hostname = socket.gethostname()

        if hostname == required_host:
            return True
        else:
            return False

    def is_it_time_to_stop(self, process_name):
        stop_time = self.get_stop_time(process_name)
        now_time = datetime.datetime.now().time()

        if now_time > stop_time:
            return True
        else:
            return False

    def run_on_completion_only(self, process_name, method_name):
        this_method_dict = self.get_method_configuration_for_process_name(
            process_name, method_name
        )
        run_on_completion_only = this_method_dict.get(
            "run_on_completion_only", False)
        run_on_completion_only = str2Bool(run_on_completion_only)

        return run_on_completion_only

    def frequency_for_process_and_method(
        self, process_name, method_name, use_strategy_config=False
    ):
        frequency, _ = self.frequency_and_max_executions_for_process_and_method(
            process_name, method_name, use_strategy_config=use_strategy_config)
        return frequency

    def max_executions_for_process_and_method(
        self, process_name, method_name, use_strategy_config
    ):
        _, max_executions = self.frequency_and_max_executions_for_process_and_method(
            process_name, method_name, use_strategy_config=use_strategy_config)
        return max_executions

    def frequency_and_max_executions_for_process_and_method(
        self, process_name, method_name, use_strategy_config=False
    ):
        """

        :param process_name:  str
        :param method_name:  str
        :return: tuple of int: frequency (minutes), max executions
        """

        if use_strategy_config:
            # the 'method' here is actually a strategy
            (
                frequency,
                max_executions,
            ) = self.frequency_and_max_executions_for_process_and_method_strategy_dict(
                process_name,
                method_name)
        else:
            (
                frequency,
                max_executions,
            ) = self.frequency_and_max_executions_for_process_and_method_process_dict(
                process_name,
                method_name)

        return frequency, max_executions

    def frequency_and_max_executions_for_process_and_method_strategy_dict(
        self, process_name, strategy_name
    ):
        this_process_dict = self.get_strategy_dict_for_process(
            process_name, strategy_name
        )
        frequency = this_process_dict.get("frequency", 60)
        max_executions = this_process_dict.get("max_executions", 1)

        return frequency, max_executions

    def get_strategy_dict_for_strategy(self, strategy_name):
        diag_strategy_config = diagStrategiesConfig(self.data)
        strategy_dict = diag_strategy_config.get_strategy_dict_for_strategy(
            strategy_name
        )

        return strategy_dict

    def frequency_and_max_executions_for_process_and_method_process_dict(
        self, process_name, method_name
    ):

        this_method_dict = self.get_method_configuration_for_process_name(
            process_name, method_name
        )
        frequency = this_method_dict.get("frequency", 60)
        max_executions = this_method_dict.get("max_executions", 1)

        return frequency, max_executions

    def get_method_configuration_for_process_name(
            self, process_name, method_name):
        all_method_dict = self.get_all_method_dict_for_process_name(
            process_name)
        this_method_dict = all_method_dict.get(method_name, {})

        return this_method_dict

    def get_all_method_dict_for_process_name(self, process_name):
        all_method_dict = self.get_configuration_item_for_process_name(
            process_name, "methods", default={}, use_config_default=False
        )

        return all_method_dict

    def previous_process_name(self, process_name):
        """

        :param process_name:
        :return: str or None
        """
        return self.get_configuration_item_for_process_name(
            process_name, "previous_process", default=None, use_config_default=False)

    def get_start_time(self, process_name):
        """
        Return time object, or 00:01 if none available
        :param process_name:
        :return:
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "start_time", default=None, use_config_default=True
        )
        if result is None:
            result = "00:01"

        result = datetime.datetime.strptime(result, "%H:%M").time()

        return result

    def how_long_in_hours_before_trading_process_finishes(self):

        now_datetime = datetime.datetime.now()

        now_date = now_datetime.date()
        stop_time = self.get_stop_time_of_trading_process()
        stop_datetime = datetime.datetime.combine(now_date, stop_time)

        diff = stop_datetime - now_datetime
        time_seconds = max(0, diff.total_seconds())
        time_hours = time_seconds / SECONDS_PER_HOUR

        return time_hours

    def get_stop_time_of_trading_process(self):
        return self.get_stop_time("run_stack_handler")

    def get_stop_time(self, process_name):
        """
        Return time object, or 00:01 if none available
        :param process_name:
        :return:
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "stop_time", default=None, use_config_default=True
        )
        if result is None:
            result = "23:50"

        result = datetime.datetime.strptime(result, "%H:%M").time()

        return result

    def required_machine_name(self, process_name):
        """

        :param process_name:
        :return: str or None
        """
        result = self.get_configuration_item_for_process_name(
            process_name, "host_name", default=None, use_config_default=False
        )

        return result

    def get_list_of_processes_run_over_strategies(self):
        return self.get_process_configuration_for_item_name(
            "run_over_strategies")

    def get_configuration_item_for_process_name(
        self, process_name, item_name, default=None, use_config_default=False
    ):
        process_config_for_item = self.get_process_configuration_for_item_name(
            item_name
        )
        config_item = process_config_for_item.get(process_name, default)
        if use_config_default and config_item is default:
            config_item = process_config_for_item.get("default", default)

        return config_item

    def get_process_configuration_for_item_name(self, item_name):
        config = getattr(self, "_process_config_%s" % item_name, None)
        if config is None:
            config = get_private_then_default_key_value(
                "process_configuration_%s" % item_name, raise_error=False
            )
            if config is missing_data:
                return {}
            setattr(self, "_process_config_%s" % item_name, config)

        return config