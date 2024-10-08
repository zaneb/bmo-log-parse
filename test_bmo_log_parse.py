import unittest

import datetime
import io

import bmo_log_parse as bmlp


class RecordTest(unittest.TestCase):
    maxDiff = None

    def test_timestamp(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        r = bmlp.Record(l)

        self.assertEqual(datetime.datetime(2020, 5, 13, 14, 23, 52, 516768,
                                           datetime.timezone.utc),
                         r.timestamp)

        output = r.format()
        self.assertEqual('2020-05-13T14:23:52.516',
                         output.format().split(' ')[0])

    def test_iso8601_timestamp(self):
        # Check timestamp format introduced (temporarily) by
        # https://github.com/metal3-io/baremetal-operator/pull/1175
        l = {"level":"info","ts":"2020-05-13T14:23:52.516Z",
             "logger":"cmd","msg":""}
        r = bmlp.Record(l)

        self.assertEqual(datetime.datetime(2020, 5, 13, 14, 23, 52, 516000,
                                           datetime.timezone.utc),
                         r.timestamp)

        output = r.format()
        self.assertEqual('2020-05-13T14:23:52.516',
                         output.format().split(' ')[0])

    def test_rfc3339_timestamp(self):
        # Check timestamp format introduced (temporarily) by
        # controller-runtime 0.14
        l = {"level":"info","ts":"2020-05-13T14:23:52Z",
             "logger":"cmd","msg":""}
        r = bmlp.Record(l)

        self.assertEqual(datetime.datetime(2020, 5, 13, 14, 23, 52, 0,
                                           datetime.timezone.utc),
                         r.timestamp)

        output = r.format()
        self.assertEqual('2020-05-13T14:23:52.000',
                         output.format().split(' ')[0])

    def test_level(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        r1 = bmlp.Record(l)
        self.assertEqual(bmlp.INFO, r1.level)

        l = {"level":"error","ts":1589379832.5167677,"logger":"cmd","msg":""}
        r2 = bmlp.Record(l)
        self.assertEqual(bmlp.ERROR, r2.level)

    def test_logger(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        r = bmlp.Record(l)

        self.assertIn(r.logger, bmlp.COMMAND)

    def test_name(self):
        c = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        cmd = bmlp.Record(c)
        self.assertIsNone(cmd.name)

        r = {"level":"info","ts":1589379832.872805,
             "logger":"controller-runtime.metrics",
             "msg":"metrics server is starting to listen",
             "addr":"127.0.0.1:8085"}
        runtime = bmlp.Record(r)
        self.assertIsNone(runtime.name)

        i = {"level":"info","ts":1589379832.873149,
             "logger":"baremetalhost_ironic","msg":"ironic settings",
             "endpoint":"http://172.30.0.47:6385/v1/",
             "inspectorEndpoint":"http://172.30.0.47:5050/v1/",
             "deployKernelURL":"http://172.30.0.47:6180/images/ipa.kernel",
             "deployRamdiskURL":"http://172.30.0.47:6180/images/initramfs"}
        ironic = bmlp.Record(i)
        self.assertIsNone(ironic.name)

        ip = {"level":"info","ts":1589380774.1379526,
              "logger":"baremetalhost_ironic",
              "msg":"validating management access","host":"somehost"}
        ironic_prov = bmlp.Record(ip)
        self.assertEqual('somehost', ironic_prov.name)

        ip_ns = {"level":"info","ts":1589380774.1379526,
                 "logger":"baremetalhost_ironic",
                 "msg":"validating management access","host":"metal3~somehost"}
        ironic_prov_ns = bmlp.Record(ip_ns)
        self.assertEqual('somehost', ironic_prov_ns.name)

        b = {"level":"info","ts":1589380774.1207273,
             "logger":"baremetalhost","msg":"Reconciling BareMetalHost",
             "Request.Namespace":"metal3","Request.Name":"somehost"}
        bmh = bmlp.Record(b)
        self.assertEqual('somehost', bmh.name)

        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        err = bmlp.Record(e)
        self.assertEqual('somehost', err.name)

        se = {"level":"error","ts":1589381055.1638162,
              "logger":"controller-runtime.source",
              "msg":"if kind is a CRD, in should be installed before calling Start",
              "kind":"BaremetalHost.metal3.io",
              "error":"no matches for kind \"BaremetalHost\" in"
                      "version \"metal3.io/v1alpha1\"",
              "stacktrace":"sigs.k8s.io/controller-runtime/pkg/source.(*Kind).Start.func1\n"
              "\t/go/src/github.com/metal3-io/baremetal-operator/vendor/sigs.k8s.io/controller-runtime/pkg/source/source.go:128"}
        err = bmlp.Record(se)
        self.assertIsNone(err.name)

        bv = {"level":"info","ts":1696185326.2182727,
              "logger":"baremetalhost-validation",
              "msg":"validate update","name":"somehost"}
        bmhv = bmlp.Record(bv)
        self.assertEqual('somehost', bmhv.name)

        sn = {"level":"info","ts":1706890740.1449683,
              "logger":"controllers.HostFirmwareSettings",
              "msg":"start",
              "hostfirmwaresettings":{"name":"somehost",
                                      "namespace":"metal3"}}
        structured_name = bmlp.Record(sn)
        self.assertEqual('somehost', structured_name.name)

    def test_name_controller_runtime(self):
        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.manager.controller.baremetalhost",
             "msg":"Reconciler error",
             "reconciler group":"metal3.io",
             "reconciler kind":"BareMetalHost",
             "namespace":"metal3",
             "name":"somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        err = bmlp.Record(e)
        self.assertEqual('somehost', err.name)

    def test_name_hfs(self):
        f = {"level":"info","ts":1644553362.482095,
             "logger":"controllers.HostFirmwareSettings",
             "msg":"start",
             "hostfirmwaresettings":"metal3/somehost"}
        hfs = bmlp.Record(f)
        self.assertEqual('somehost', hfs.name)

    def test_name_ppimg(self):
        i = {"level":"info","ts":1643928194.57431,
             "logger":"controllers.PreprovisioningImage",
             "msg":"updating status",
             "preprovisioningimage":"metal3/somehost"}
        image = bmlp.Record(i)
        self.assertEqual('somehost', image.name)

    def test_namespace(self):
        c = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        cmd = bmlp.Record(c)
        self.assertIsNone(cmd.name)

        r = {"level":"info","ts":1589379832.872805,
             "logger":"controller-runtime.metrics",
             "msg":"metrics server is starting to listen",
             "addr":"127.0.0.1:8085"}
        runtime = bmlp.Record(r)
        self.assertIsNone(runtime.namespace)

        i = {"level":"info","ts":1589379832.873149,
             "logger":"baremetalhost_ironic","msg":"ironic settings",
             "endpoint":"http://172.30.0.47:6385/v1/",
             "inspectorEndpoint":"http://172.30.0.47:5050/v1/",
             "deployKernelURL":"http://172.30.0.47:6180/images/ipa.kernel",
             "deployRamdiskURL":"http://172.30.0.47:6180/images/initramfs"}
        ironic = bmlp.Record(i)
        self.assertIsNone(ironic.namespace)

        ip = {"level":"info","ts":1589380774.1379526,
              "logger":"baremetalhost_ironic",
              "msg":"validating management access","host":"somehost"}
        ironic_prov = bmlp.Record(ip)
        self.assertEqual(None, ironic_prov.namespace)

        ip_ns = {"level":"info","ts":1589380774.1379526,
                 "logger":"baremetalhost_ironic",
                 "msg":"validating management access","host":"metal3~somehost"}
        ironic_prov_ns = bmlp.Record(ip_ns)
        self.assertEqual('metal3', ironic_prov_ns.namespace)

        b = {"level":"info","ts":1589380774.1207273,
             "logger":"baremetalhost","msg":"Reconciling BareMetalHost",
             "Request.Namespace":"metal3","Request.Name":"somehost"}
        bmh = bmlp.Record(b)
        self.assertEqual('metal3', bmh.namespace)

        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        err = bmlp.Record(e)
        self.assertEqual('metal3', err.namespace)

        sn = {"level":"info","ts":1706890740.1449683,
              "logger":"controllers.HostFirmwareSettings",
              "msg":"start",
              "hostfirmwaresettings":{"name":"somehost",
                                      "namespace":"metal3"}}
        structured_name = bmlp.Record(sn)
        self.assertEqual('metal3', structured_name.namespace)

    def test_namespace_controller_runtime(self):
        ip_ns = {"level":"info","ts":1589380774.1379526,
                 "logger":"provisioner.ironic",
                 "msg":"validating management access",
                 "host":"metal3~somehost"}
        ironic_prov_ns = bmlp.Record(ip_ns)
        self.assertEqual('metal3', ironic_prov_ns.namespace)

        b = {"level":"info","ts":1589380774.1207273,
             "logger":"controllers.BareMetalHost","msg":"start",
             "baremetalhost":"metal3/somehost"}
        bmh = bmlp.Record(b)
        self.assertEqual('metal3', bmh.namespace)

        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.manager.controller.baremetalhost",
             "msg":"Reconciler error",
             "reconciler group":"metal3.io",
             "reconciler kind":"BareMetalHost",
             "namespace":"metal3",
             "name":"somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        err = bmlp.Record(e)
        self.assertEqual('metal3', err.namespace)

    def test_message(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd",
             "msg":"Go Version: go1.13.8"}
        r = bmlp.Record(l)

        self.assertEqual('Go Version: go1.13.8', r.message)

    def test_stacktrace(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":""}
        r1 = bmlp.Record(l)
        self.assertIsNone(r1.context)

        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r2 = bmlp.Record(e)
        self.assertEqual('github.com/go-logr/zapr.(*zapLogger).Error\n'
                         '\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/'
                         'zapr.go:128',
                         r2.context)

    def test_hardware_details(self):
        l = {"level":"info","ts":1590157176.3108344,
             "logger":"baremetalhost_ironic",
             "msg":"received introspection data",
             "data":{"cpu":{"architecture":"x86_64","count":1}}}
        r = bmlp.Record(l)
        self.assertEqual('cpu:\n  architecture: x86_64\n  count: 1\n',
                         r.context)

    def test_data(self):
        b = {"level":"info","ts":1589380774.1207273,
             "logger":"baremetalhost","msg":"Reconciling BareMetalHost",
             "Request.Namespace":"metal3","Request.Name":"somehost"}
        r = bmlp.Record(b)

        self.assertSetEqual({'Request.Namespace', 'Request.Name'},
                            set(r.data.keys()))

    def test_error_data(self):
        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "errorVerbose":"The error message and the stack trace "
             "concatenated for no good reason",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(e)

        self.assertSetEqual({'controller', 'request'},
                            set(r.data.keys()))

    def test_format(self):
        l = {"level":"info","ts":1589379832.5167677,"logger":"cmd",
             "msg":"Go Version: go1.13.8"}
        r = bmlp.Record(l)

        self.assertEqual('2020-05-13T14:23:52.516 Go Version: go1.13.8',
                         r.format())

    def test_format_data(self):
        l = {"level":"info","ts":1589379832.873149,
             "logger":"baremetalhost_ironic","msg":"ironic settings",
             "endpoint":"http://172.30.0.47:6385/v1/",
             "inspectorEndpoint":"http://172.30.0.47:5050/v1/",
             "deployKernelURL":"http://172.30.0.47:6180/images/ipa.kernel",
             "deployRamdiskURL":"http://172.30.0.47:6180/images/initramfs"}
        r = bmlp.Record(l)

        self.assertEqual(
            '2020-05-13T14:23:52.873 ironic settings {'
            "endpoint: 'http://172.30.0.47:6385/v1/', "
            "inspectorEndpoint: 'http://172.30.0.47:5050/v1/', "
            "deployKernelURL: 'http://172.30.0.47:6180/images/ipa.kernel', "
            "deployRamdiskURL: 'http://172.30.0.47:6180/images/initramfs'}",
            r.format())

    def test_format_highlight(self):
        l = {"level":"info","ts":1589379832.873149,
             "logger":"baremetalhost_ironic","msg":"ironic settings",
             "endpoint":"http://172.30.0.47:6385/v1/",
             "inspectorEndpoint":"http://172.30.0.47:5050/v1/",
             "deployKernelURL":"http://172.30.0.47:6180/images/ipa.kernel",
             "deployRamdiskURL":"http://172.30.0.47:6180/images/initramfs"}
        r = bmlp.Record(l)

        self.assertEqual(
            '\033[37m2020-05-13T14:23:52.873 \033[39mironic settings\033[37m {'
            "endpoint: 'http://172.30.0.47:6385/v1/', "
            "inspectorEndpoint: 'http://172.30.0.47:5050/v1/', "
            "deployKernelURL: 'http://172.30.0.47:6180/images/ipa.kernel', "
            "deployRamdiskURL: 'http://172.30.0.47:6180/images/initramfs'}"
            "\033[39m",
            r.format(highlight=True))

    def test_format_noextra_highlight(self):
        l = {"level":"info","ts":1589379832.873149,
             "logger":"baremetalhost_ironic","msg":"ironic settings"}
        r = bmlp.Record(l)

        self.assertEqual(
            '\033[37m2020-05-13T14:23:52.873 \033[39mironic settings\033[39m',
            r.format(highlight=True))

    def test_format_stacktrace(self):
        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "errorVerbose":"The error message and the stack trace "
             "concatenated for no good reason",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(e)

        self.assertEqual(
            '2020-05-13T14:44:15.163 Reconciler error {'
            "controller: 'metal3-baremetalhost-controller', "
            "request: 'metal3/somehost'}\n"
            'failed to save host status after "ready".\n'
            'github.com/go-logr/zapr.(*zapLogger).Error\n'
            '\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128',
            r.format())

    def test_format_error_verbose_stacktrace(self):
        e = {"level":"error","ts":"2023-04-07T11:57:12.235Z",
             "msg":"Reconciler error",
             "controller":"baremetalhost",
             "controllerGroup":"metal3.io",
             "controllerKind":"BareMetalHost",
             "BareMetalHost":{"name":"somehost","namespace":"metal3"},
             "namespace":"metal3",
             "name":"somehost",
             "reconcileID":"ddb00718-a6c5-4f56-9470-75ef509b68ec",
             "error":"action \"unmanaged\" failed: failed to determine stuff",
             "errorVerbose":"missing BMC address\n"
             "github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128\n"
             "runtime.goexit\n"
             "\t/usr/lib/golang/src/runtime/asm_amd64.s:1594\n",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(e)

        self.assertEqual(
            '2023-04-07T11:57:12.235 Reconciler error {'
            "controller: 'baremetalhost', "
            "namespace: 'metal3', name: 'somehost'}\n"
            'action \"unmanaged\" failed: failed to determine stuff\n'
            'missing BMC address\n'
            'github.com/go-logr/zapr.(*zapLogger).Error\n'
            '\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128\n'
            'runtime.goexit\n'
            '\t/usr/lib/golang/src/runtime/asm_amd64.s:1594\n',
            r.format(verbose=True))

    def test_format_error_highlight(self):
        e = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "request": "metal3/somehost"}
        r = bmlp.Record(e)

        self.assertEqual(
            '\033[91m2020-05-13T14:44:15.163 \033[31mReconciler error\033[91m '
            "{request: 'metal3/somehost'}\033[39m",
            r.format(highlight=True))

    def test_format_stacktrace_highlight(self):
        l = {"level":"info","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(l)

        self.assertEqual(
            '\033[37m2020-05-13T14:44:15.163 '
            '\033[39mReconciler error\033[37m {'
            "controller: 'metal3-baremetalhost-controller', "
            "request: 'metal3/somehost'}\033[39m\n"
            '\033[90mgithub.com/go-logr/zapr.(*zapLogger).Error\033[39m\n'
            '\033[90m\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/'
            'zapr.go:128\033[39m',
            r.format(highlight=True))

    def test_format_error_stacktrace_highlight(self):
        l = {"level":"error","ts":1589381055.1638162,
             "logger":"controller-runtime.controller",
             "msg":"Reconciler error",
             "controller":"metal3-baremetalhost-controller",
             "request":"metal3/somehost",
             "error":"failed to save host status after \"ready\".",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(l)

        self.assertEqual(
            '\033[91m2020-05-13T14:44:15.163 '
            '\033[31mReconciler error\033[91m {'
            "controller: 'metal3-baremetalhost-controller', "
            "request: 'metal3/somehost'}\033[39m\n"
            '\033[31mfailed to save host status after "ready".\033[39m\n'
            '\033[90mgithub.com/go-logr/zapr.(*zapLogger).Error\033[39m\n'
            '\033[90m\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/'
            'zapr.go:128\033[39m',
            r.format(highlight=True))

    def test_format_error_verbose_stacktrace_highlight(self):
        e = {"level":"error","ts":"2023-04-07T11:57:12.235Z",
             "msg":"Reconciler error",
             "controller":"baremetalhost",
             "controllerGroup":"metal3.io",
             "controllerKind":"BareMetalHost",
             "BareMetalHost":{"name":"somehost","namespace":"metal3"},
             "namespace":"metal3",
             "name":"somehost",
             "reconcileID":"ddb00718-a6c5-4f56-9470-75ef509b68ec",
             "error":"action \"unmanaged\" failed: failed to determine stuff",
             "errorVerbose":"missing BMC address\n"
             "github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128\n"
             "runtime.goexit\n"
             "\t/usr/lib/golang/src/runtime/asm_amd64.s:1594\n",
             "stacktrace":"github.com/go-logr/zapr.(*zapLogger).Error\n"
             "\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/zapr.go:128"}
        r = bmlp.Record(e)

        self.assertEqual(
            '\033[91m2023-04-07T11:57:12.235 '
            '\033[31mReconciler error\033[91m {'
            "controller: 'baremetalhost', "
            "namespace: 'metal3', name: 'somehost'}\033[39m\n"
            '\033[31maction \"unmanaged\" failed: '
            'failed to determine stuff\033[39m\n'
            '\033[90mmissing BMC address\033[39m\n'
            '\033[90mgithub.com/go-logr/zapr.(*zapLogger).Error\033[39m\n'
            '\033[90m\t/go/pkg/mod/github.com/go-logr/zapr@v0.1.1/'
            'zapr.go:128\033[39m\n'
            '\033[90mruntime.goexit\033[39m\n'
            '\033[90m\t/usr/lib/golang/src/runtime/asm_amd64.s:1594\033[39m',
            r.format(verbose=True, highlight=True))


class TestRead(unittest.TestCase):
    log = """
{"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":"Go Version: go1.13.8"}
{"level":"info","ts":1589379832.872805,"logger":"controller-runtime.metrics","msg":"metrics server is starting to listen","addr":"127.0.0.1:8085"}
{"level":"info","ts":1589379832.873149,"logger":"baremetalhost_ironic","msg":"ironic settings","endpoint":"http://172.30.0.47:6385/v1/","inspectorEndpoint":"http://172.30.0.47:5050/v1/","deployKernelURL":"http://172.30.0.47:6180/images/ironic-python-agent.kernel","deployRamdiskURL":"http://172.30.0.47:6180/images/ironic-python-agent.initramfs"}
I0513 14:23:52.873384       1 leaderelection.go:241] attempting to acquire leader lease  metal3/baremetal-operator...
I0513 14:23:52.882595       1 leaderelection.go:251] successfully acquired lease metal3/baremetal-operator
{"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"ahost"}
{"level":"info","ts":1589380774.1207843,"logger":"baremetalhost","msg":"adding finalizer","Request.Namespace":"metal3","Request.Name":"ahost","existingFinalizers":[],"newValue":"baremetalhost.metal3.io"}
{"level":"info","ts":1589380774.1288416,"logger":"baremetalhost","msg":"changing provisioning state","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","old":"","new":"registering"}
{"level":"info","ts":1589380774.128888,"logger":"baremetalhost","msg":"saving host status","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","operational status":"OK","provisioning state":"registering"}
{"level":"info","ts":1589380774.1379526,"logger":"baremetalhost_ironic","msg":"validating management access","host":"bsr22ar07c018"}
{"level":"info","ts":1589380774.1379595,"logger":"baremetalhost_ironic","msg":"looking for existing node by name","host":"bsr22ar07c018","name":"bsr22ar07c018"}
{"level":"info","ts":1589380774.2415836,"logger":"baremetalhost_ironic","msg":"registering host in ironic","host":"bsr22ar07c018"}
{"level":"info","ts":1589380774.8010514,"logger":"baremetalhost_ironic","msg":"changing provisioning state","host":"bsr22ar07c018","current":"enroll","existing target":"","new target":"manage"}
{"level":"info","ts":1589380774.8608532,"logger":"baremetalhost","msg":"response from validate","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","provResult":{"Dirty":true,"RequeueAfter":10000000000,"ErrorMessage":""}}
{"level":"info","ts":1589380774.8704467,"logger":"baremetalhost","msg":"done","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","requeue":true,"after":10}
{"level":"info","ts":1607045743.4722486,"msg":"Operator Concurrency will be set to a default value of 3"}
"""

    def test_read_records(self):
        input_stream = io.StringIO(self.log)
        records = list(bmlp.read_records(input_stream))
        self.assertEqual(14, len(records))
        for r in records:
            self.assertIsInstance(r, bmlp.Record)

    def test_process_log(self):
        input_stream = io.StringIO(self.log)
        output_stream = io.StringIO()
        bmlp.process_log(input_stream, [], output_stream)
        output_stream.seek(0)
        output = output_stream.readlines()
        self.assertEqual(14, len(output))
        for l in output:
            self.assertTrue(l.startswith('2020-'))


class TestReadWithTimestamps(TestRead):
    # must-gather logs from OpenShift are prepended with an ISO8601 timestamp
    log = """
2020-05-13T14:23:52.5167677Z {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":"Go Version: go1.13.8"}
2020-05-13T14:23:52.8728050Z {"level":"info","ts":1589379832.872805,"logger":"controller-runtime.metrics","msg":"metrics server is starting to listen","addr":"127.0.0.1:8085"}
2020-05-13T14:23:52.8731490Z {"level":"info","ts":1589379832.873149,"logger":"baremetalhost_ironic","msg":"ironic settings","endpoint":"http://172.30.0.47:6385/v1/","inspectorEndpoint":"http://172.30.0.47:5050/v1/","deployKernelURL":"http://172.30.0.47:6180/images/ironic-python-agent.kernel","deployRamdiskURL":"http://172.30.0.47:6180/images/ironic-python-agent.initramfs"}
2020-05-13T14:23:52.8733840Z I0513 14:23:52.873384       1 leaderelection.go:241] attempting to acquire leader lease  metal3/baremetal-operator...
2020-05-13T14:23:52.8825951Z I0513 14:23:52.882595       1 leaderelection.go:251] successfully acquired lease metal3/baremetal-operator
2020-05-13T14:39:34.1207273Z {"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"ahost"}
2020-05-13T14:39:34.1207843Z {"level":"info","ts":1589380774.1207843,"logger":"baremetalhost","msg":"adding finalizer","Request.Namespace":"metal3","Request.Name":"ahost","existingFinalizers":[],"newValue":"baremetalhost.metal3.io"}
2020-05-13T14:39:34.1284160Z {"level":"info","ts":1589380774.1288416,"logger":"baremetalhost","msg":"changing provisioning state","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","old":"","new":"registering"}
2020-05-13T14:39:34.1288880Z {"level":"info","ts":1589380774.128888,"logger":"baremetalhost","msg":"saving host status","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","operational status":"OK","provisioning state":"registering"}
2020-05-13T14:39:34.1379526Z {"level":"info","ts":1589380774.1379526,"logger":"baremetalhost_ironic","msg":"validating management access","host":"bsr22ar07c018"}
2020-05-13T14:39:34.1379595Z {"level":"info","ts":1589380774.1379595,"logger":"baremetalhost_ironic","msg":"looking for existing node by name","host":"bsr22ar07c018","name":"bsr22ar07c018"}
2020-05-13T14:39:34.2415836Z {"level":"info","ts":1589380774.2415836,"logger":"baremetalhost_ironic","msg":"registering host in ironic","host":"bsr22ar07c018"}
2020-05-13T14:39:34.8010514Z {"level":"info","ts":1589380774.8010514,"logger":"baremetalhost_ironic","msg":"changing provisioning state","host":"bsr22ar07c018","current":"enroll","existing target":"","new target":"manage"}
2020-05-13T14:39:34.8608532Z {"level":"info","ts":1589380774.8608532,"logger":"baremetalhost","msg":"response from validate","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","provResult":{"Dirty":true,"RequeueAfter":10000000000,"ErrorMessage":""}}
2020-05-13T14:39:34.8704467Z {"level":"info","ts":1589380774.8704467,"logger":"baremetalhost","msg":"done","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","requeue":true,"after":10}
2020-12-04T01:35:43.472254864Z {"level":"info","ts":1607045743.4722486,"msg":"Operator Concurrency will be set to a default value of 3"}
"""


class TestReadRotated(TestRead):
    # must-gather logs from OpenShift that have been rotated are prepended with
    # a different ISO8601 timestamp and some other garbage
    log = """
2020-05-13T14:23:52.5167677+00:00 stderr F {"level":"info","ts":1589379832.5167677,"logger":"cmd","msg":"Go Version: go1.13.8"}
2020-05-13T14:23:52.8728050+00:00 stderr F {"level":"info","ts":1589379832.872805,"logger":"controller-runtime.metrics","msg":"metrics server is starting to listen","addr":"127.0.0.1:8085"}
2020-05-13T14:23:52.8731490+00:00 stderr F {"level":"info","ts":1589379832.873149,"logger":"baremetalhost_ironic","msg":"ironic settings","endpoint":"http://172.30.0.47:6385/v1/","inspectorEndpoint":"http://172.30.0.47:5050/v1/","deployKernelURL":"http://172.30.0.47:6180/images/ironic-python-agent.kernel","deployRamdiskURL":"http://172.30.0.47:6180/images/ironic-python-agent.initramfs"}
2020-05-13T14:23:52.8733840+00:00 stderr F I0513 14:23:52.873384       1 leaderelection.go:241] attempting to acquire leader lease  metal3/baremetal-operator...
2020-05-13T14:23:52.8825951+00:00 stderr F I0513 14:23:52.882595       1 leaderelection.go:251] successfully acquired lease metal3/baremetal-operator
2020-05-13T14:39:34.1207273+00:00 stderr F {"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"ahost"}
2020-05-13T14:39:34.1207843+00:00 stderr F {"level":"info","ts":1589380774.1207843,"logger":"baremetalhost","msg":"adding finalizer","Request.Namespace":"metal3","Request.Name":"ahost","existingFinalizers":[],"newValue":"baremetalhost.metal3.io"}
2020-05-13T14:39:34.1284160+00:00 stderr F {"level":"info","ts":1589380774.1288416,"logger":"baremetalhost","msg":"changing provisioning state","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","old":"","new":"registering"}
2020-05-13T14:39:34.1288880+00:00 stderr F {"level":"info","ts":1589380774.128888,"logger":"baremetalhost","msg":"saving host status","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"","operational status":"OK","provisioning state":"registering"}
2020-05-13T14:39:34.1379526+00:00 stderr F {"level":"info","ts":1589380774.1379526,"logger":"baremetalhost_ironic","msg":"validating management access","host":"bsr22ar07c018"}
2020-05-13T14:39:34.1379595+00:00 stderr F {"level":"info","ts":1589380774.1379595,"logger":"baremetalhost_ironic","msg":"looking for existing node by name","host":"bsr22ar07c018","name":"bsr22ar07c018"}
2020-05-13T14:39:34.2415836+00:00 stderr F {"level":"info","ts":1589380774.2415836,"logger":"baremetalhost_ironic","msg":"registering host in ironic","host":"bsr22ar07c018"}
2020-05-13T14:39:34.8010514+00:00 stderr F {"level":"info","ts":1589380774.8010514,"logger":"baremetalhost_ironic","msg":"changing provisioning state","host":"bsr22ar07c018","current":"enroll","existing target":"","new target":"manage"}
2020-05-13T14:39:34.8608532+00:00 stderr F {"level":"info","ts":1589380774.8608532,"logger":"baremetalhost","msg":"response from validate","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","provResult":{"Dirty":true,"RequeueAfter":10000000000,"ErrorMessage":""}}
2020-05-13T14:39:34.8704467+00:00 stderr F {"level":"info","ts":1589380774.8704467,"logger":"baremetalhost","msg":"done","Request.Namespace":"metal3","Request.Name":"bsr22ar07c018","provisioningState":"registering","requeue":true,"after":10}
2020-12-04T01:35:43.472254864+00:00 stderr F {"level":"info","ts":1607045743.4722486,"msg":"Operator Concurrency will be set to a default value of 3"}
"""


class TestParseTime(unittest.TestCase):
    def test_date_only(self):
        self.assertEqual(datetime.datetime(2020, 5, 19),
                         bmlp.parse_datetime('2020-05-19'))

    def test_minute(self):
        self.assertEqual(datetime.datetime(2020, 5, 19, 13, 27, 0),
                         bmlp.parse_datetime('2020-05-19T13:27'))

    def test_second(self):
        self.assertEqual(datetime.datetime(2020, 5, 19, 13, 27, 49),
                         bmlp.parse_datetime('2020-05-19T13:27:49'))

    def test_microsecond(self):
        self.assertEqual(datetime.datetime(2020, 5, 19, 13, 27, 49, 32000),
                         bmlp.parse_datetime('2020-05-19T13:27:49.032'))


class TestFilter(unittest.TestCase):
    log = """
{"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380774.1258268,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380774.1339087,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"info","ts":1589380774.1378222,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"info","ts":1589380774.870522,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"bar"}
{"level":"error","ts":1589380775.0094552,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"error","ts":1589380775.0401566,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"metal3~foo"}
{"level":"info","ts":1589380775.070861,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380775.099308,"logger":"controllers.BareMetalHost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380776.36193,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal4","Request.Name":"foo"}
{"level":"info","ts":1643928194.57431,"logger":"controllers.PreprovisioningImage","msg":"updating status","preprovisioningimage":"metal5/wibble"}
{"level":"info","ts":1644553362.482095,"logger":"controllers.HostFirmwareSettings","msg":"start","hostfirmwaresettings":"metal5/wibble"}
{"level":"info","ts":1644566317.4338849,"logger":"controllers.BMCEventSubscription","msg":"start","bmceventsubscription":"metal5/wibble"}
{"level":"info","ts":1696185326.2182565,"logger":"webhooks.BareMetalHost","msg":"validate update","name":"blarg","namespace":"metal3"}
{"level":"info","ts":1696185326.2182565,"logger":"baremetalhost-resource","msg":"validate update","name":"blarg"}
{"level":"info","ts":1696185326.2182727,"logger":"baremetalhost-validation","msg":"validate update","name":"blarg"}
{"level":"info","ts":1696185326.2333705,"logger":"webhooks.BMCEventSubscription","msg":"validate create","name":"blarg","namespace":"metal3"}
{"level":"info","ts":1696185326.2333705,"logger":"bmceventsubscription-resource","msg":"validate create","name":"blarg"}
{"level":"info","ts":1696185326.2333896,"logger":"bmceventsubscription-validation","msg":"validate create","name":"blarg"}
{"level":"info","ts":1717769018.3849478,"logger":"controllers.HostFirmwareComponents","msg":"start","hostfirmwarecomponents":{"name":"worker-01","namespace":"openshift-machine-api"}}
"""

    def setUp(self):
        self.stream = io.StringIO(self.log)

    def test_no_filter(self):
        f = bmlp.get_filters(bmlp.get_options([]))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(20, len(r))

    def test_filter_name(self):
        f = bmlp.get_filters(bmlp.get_options(['--name=foo']))
        r1 = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(4, len(r1))

    def test_filter_namespace(self):
        f = bmlp.get_filters(bmlp.get_options(['--namespace=metal3']))
        r1 = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(10, len(r1))

    def test_filter_error(self):
        f = bmlp.get_filters(bmlp.get_options(['--error']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(4, len(r))

    def test_filter_controller(self):
        f = bmlp.get_filters(bmlp.get_options(['--controller-only']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(12, len(r))

    def test_filter_controller_bmh(self):
        f = bmlp.get_filters(bmlp.get_options(['--controller-only=bmh']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(8, len(r))

    def test_filter_controller_ppimg(self):
        f = bmlp.get_filters(bmlp.get_options(['--controller-only=ppimg']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(1, len(r))

    def test_filter_controller_hfs(self):
        f = bmlp.get_filters(bmlp.get_options(['--controller-only=hfs']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(1, len(r))

    def test_filter_controller_hfc(self):
        f = bmlp.get_filters(bmlp.get_options([
            '--controller-only=hostfirmwarecomponents',
        ]))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(1, len(r))

    def test_filter_controller_bmcevent(self):
        f = bmlp.get_filters(bmlp.get_options(['--controller-only=bmcevent']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(1, len(r))

    def test_filter_provisioner(self):
        f = bmlp.get_filters(bmlp.get_options(['--provisioner-only']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(2, len(r))

    def test_filter_webhook(self):
        f = bmlp.get_filters(bmlp.get_options(['--webhook-only']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(6, len(r))

    def test_filter_webhook_bmh(self):
        f = bmlp.get_filters(bmlp.get_options(['--webhook-only=bmh']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(3, len(r))

    def test_filter_webhook_bmcevent(self):
        f = bmlp.get_filters(bmlp.get_options(['--webhook-only=bmcevent']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(3, len(r))

    def test_filter_start(self):
        f = bmlp.get_filters(bmlp.get_options(['--start=2020-05-13T14:39:35']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(15, len(r))

    def test_filter_end(self):
        f = bmlp.get_filters(bmlp.get_options(['--end=2020-05-13T14:39:36']))
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(9, len(r))

    def test_filter_start_end(self):
        o = bmlp.get_options([
            '--start=2020-05-13T14:39:35',
            '--end=2020-05-13T14:39:36',
        ])
        f = bmlp.get_filters(o)
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(4, len(r))

    def test_filter_combine_1(self):
        o = bmlp.get_options(['--name=foo', '--error', '--controller-only'])
        f = bmlp.get_filters(o)
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(1, len(r))

    def test_filter_combine_2(self):
        o = bmlp.get_options(['--name=foo', '--start=2020-05-13T14:39:35'])
        f = bmlp.get_filters(o)
        r = list(bmlp.filtered_records(self.stream, f))
        self.assertEqual(3, len(r))


class ListNamesTest(unittest.TestCase):
    log = """
{"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380774.1258268,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380774.1339087,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"info","ts":1589380774.1378222,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"info","ts":1589380774.870522,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"bar"}
{"level":"error","ts":1589380775.0094552,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"error","ts":1589380775.0401566,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"metal3~foo"}
{"level":"info","ts":1589380775.070861,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380775.099308,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380776.36193,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
"""

    def test_list_host_names(self):
        input_stream = io.StringIO(self.log)
        output_stream = io.StringIO()
        bmlp.list_host_names(input_stream, [], output_stream)
        output_stream.seek(0)
        output = output_stream.readlines()
        self.assertListEqual(['foo\n', 'bar\n', 'baz\n'], output)


class ListNamespacesTest(unittest.TestCase):
    log = """
{"level":"info","ts":1589380774.1207273,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380774.1258268,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380774.1339087,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal4","Request.Name":"baz"}
{"level":"info","ts":1589380774.1378222,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal4","Request.Name":"baz"}
{"level":"info","ts":1589380774.870522,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"bar"}
{"level":"error","ts":1589380775.0094552,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"baz"}
{"level":"error","ts":1589380775.0401566,"logger":"baremetalhost_ironic","msg":"Reconciling BareMetalHost","host":"metal5~foo"}
{"level":"info","ts":1589380775.070861,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"bar"}
{"level":"info","ts":1589380775.099308,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
{"level":"error","ts":1589380776.36193,"logger":"baremetalhost","msg":"Reconciling BareMetalHost","Request.Namespace":"metal3","Request.Name":"foo"}
"""

    def test_list_host_names(self):
        input_stream = io.StringIO(self.log)
        output_stream = io.StringIO()
        bmlp.list_host_namespaces(input_stream, [], output_stream)
        output_stream.seek(0)
        output = output_stream.readlines()
        self.assertListEqual(['metal3\n', 'metal4\n', 'metal5\n'], output)
