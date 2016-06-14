from error import *
import logging

l = logging.getLogger("aegg.analyzer")


class Analyzer(object):
    MIN_BUF_SIZE = 20

    def __init__(self):
        self.paths = []
        self.results = []

    def _new_result(self):
        return {
            'ip_symbolic': False,
            'ip_controled_name': '',
            'buf_addrs': [],
        }

    def _fully_symbolic(self, state, variable):
        for i in range(state.arch.bits):
            if not state.se.symbolic(variable[i]):
                return False
        return True

    def _check_continuity(self, address, all_address):
        i = 0
        while True:
            if not address + i in all_address:
                return address, i
            i += 1

    def _get_buf_addrs(self, state):
        # TODO: check more simfiles
        stdin_file = state.posix.get_file(0)

        sym_addrs = []
        for var in stdin_file.variables():
            sym_addrs.extend(state.memory.addrs_for_name(var))

        buf_addrs = []
        for addr in sym_addrs:
            addr, length = self._check_continuity(addr, sym_addrs)
            if length >= Analyzer.MIN_BUF_SIZE:
                buf_addrs.append({'addr': addr, 'length': length})
        return buf_addrs

    def _analyze(self, path):
        result = self._new_result()
        state = path.state
        result['ip_symbolic'] = self._fully_symbolic(state, state.ip)
        l.debug('Checking ip %s symbolic: %s' %
                (str(state.ip), result['ip_symbolic']))
        if result['ip_symbolic']:
            if state.ip.op == 'Extract':
                result['ip_controled_name'] = state.ip.args[2].args[0]
            else:
                raise AnalyzerError('ip: %s, ip.op != \'extract\'' % state.ip)
            result['buf_addrs'] = self._get_buf_addrs(state)
            l.debug('Finding %d buffers.' % len(result['buf_addrs']))
        return result

    def analyze(self, path):
        result = self._analyze(path)
        self.paths.append(path)
        self.results.append(result)
        return result
